#!/usr/bin/env python3
"""
Sensor component for Cryptoinfo
Author: Johnny Visser
"""

import requests
import time
import traceback
from datetime import datetime

from .const.const import (
    _LOGGER,
    CONF_EXTRA_SENSOR_PROPERTY,
    SENSOR_PREFIX,
    ATTR_LAST_UPDATE,
    ATTR_24H_VOLUME,
    ATTR_BASE_PRICE,
    ATTR_1H_CHANGE,
    ATTR_24H_CHANGE,
    ATTR_7D_CHANGE,
    ATTR_30D_CHANGE,
    ATTR_MARKET_CAP,
    ATTR_CIRCULATING_SUPPLY,
    ATTR_TOTAL_SUPPLY,
    ATTR_ALL_TIME_HIGH,
    ATTR_ALL_TIME_HIGH_DISTANCE,
    ATTR_ALL_TIME_LOW,
    ATTR_24H_LOW,
    ATTR_24H_HIGH,
    ATTR_IMAGE_URL,
    ATTR_DIFFICULTY,
    ATTR_HASHRATE,
    ATTR_HASHRATE_CALC,
    ATTR_POOL_CONTROL_1000B,
    ATTR_POOL_CONTROL_1000B_PERC,
    ATTR_BLOCK_HEIGHT,
    ATTR_DIFFICULTY_BLOCK_PROGRESS,
    ATTR_DIFFICULTY_RETARGET_HEIGHT,
    ATTR_DIFFICULTY_RETARGET_SECONDS,
    ATTR_DIFFICULTY_RETARGET_PERCENT_CHANGE,
    ATTR_DIFFICULTY_RETARGET_ESTIMATED_DIFF,
    ATTR_WORKER_COUNT,
    ATTR_LAST_BLOCK,
    ATTR_BLOCKS_PENDING,
    ATTR_BLOCKS_CONFIRMED,
    ATTR_BLOCKS_ORPHANED,
    ATTR_BLOCK_TIME_IN_SECONDS,
    API_BASE_URL_COINGECKO,
    API_BASE_URL_CRYPTOID,
    API_ENDPOINT_PRICE_MAIN,
    API_ENDPOINT_PRICE_ALT,
    API_ENDPOINT_DOMINANCE,
    API_ENDPOINT_CHAIN_SUMMARY,
    API_ENDPOINT_CHAIN_CONTROL,
    API_ENDPOINT_CHAIN_ORPHANS,
    API_ENDPOINT_CHAIN_BLOCK_TIME,
    API_ENDPOINT_NOMP_POOL_STATS,
    DEFAULT_CHAIN_DIFFICULTY_WINDOW,
    DEFAULT_CHAIN_DIFF_MULTIPLIER,
    DEFAULT_CHAIN_BLOCK_TIME_MINS,
    DAY_SECONDS,
)

from .manager import CryptoInfoEntityManager, CryptoInfoDataFetchType

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_ID,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity


class CryptoinfoSensor(Entity):
    def __init__(
        self,
        hass,
        cryptocurrency_name,
        currency_name,
        unit_of_measurement,
        multiplier,
        update_frequency,
        id_name,
        unique_id=None,
        state_class=None,
        api_mode="",
        pool_prefix=[""],
        fetch_args="",
        extra_sensors="",
        api_domain_name="",
        pool_name="",
        diff_multiplier="",
        block_time_minutes="",
        difficulty_window="",
        is_child_sensor=False,
    ):
        # Internal Properties
        self.hass = hass
        self.data = None
        self.cryptocurrency_name = cryptocurrency_name
        self.currency_name = currency_name
        self.pool_prefixes = pool_prefix if isinstance(pool_prefix, list) else [pool_prefix]
        self.multiplier = multiplier
        self._diff_multiplier = int(diff_multiplier) if diff_multiplier.isdigit() else DEFAULT_CHAIN_DIFF_MULTIPLIER
        self._block_time_minutes = float(block_time_minutes) if block_time_minutes.replace(
            ".", "", 1).isdigit() else DEFAULT_CHAIN_BLOCK_TIME_MINS
        self._difficulty_window = int(difficulty_window) if difficulty_window.isdigit() else DEFAULT_CHAIN_DIFFICULTY_WINDOW
        self._internal_id_name = id_name if id_name is not None else ""
        self._fetch_type = CryptoInfoEntityManager.instance().get_fetch_type_from_str(api_mode)
        self._fetch_args = fetch_args if fetch_args and len(fetch_args) else None
        self._api_domain_name = api_domain_name if api_domain_name and len(api_domain_name) else None
        self._pool_name = pool_name if pool_name and len(pool_name) else None
        self._update_frequency = update_frequency
        self._is_child_sensor = is_child_sensor
        self._child_sensors = list()
        self._child_sensor_config = extra_sensors

        # HASS Attributes
        self.update = Throttle(update_frequency)(self._update)
        self._attr_unique_id = unique_id if unique_id is not None and len(unique_id) else self._build_unique_id()
        self._name = self._build_name()
        self._state = None
        self._last_update = None
        self._icon = "mdi:bitcoin"
        self._attr_device_class = self._build_device_class()
        self._attr_state_class = state_class or SensorStateClass.MEASUREMENT
        self._attr_available = True
        self._unit_of_measurement = unit_of_measurement

        # Sensor Attributes
        self._base_price = None
        self._24h_volume = None
        self._1h_change = None
        self._24h_change = None
        self._7d_change = None
        self._30d_change = None
        self._market_cap = None
        self._circulating_supply = None
        self._total_supply = None
        self._all_time_high = None
        self._all_time_low = None
        self._24h_low = None
        self._24h_high = None
        self._image_url = None
        self._difficulty = None
        self._hashrate = None
        self._pool_control_1000b = None
        self._block_height = None
        self._worker_count = None
        self._last_block = None
        self._blocks_pending = None
        self._blocks_confirmed = None
        self._blocks_orphaned = None

    @property
    def is_child_sensor(self):
        return self._is_child_sensor

    @property
    def update_frequency(self):
        return self._update_frequency

    @property
    def fetch_type(self):
        return self._fetch_type

    @property
    def hashrate(self):
        return self._hashrate

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def available(self):
        return self._attr_available

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def state(self):
        return self._state

    @property
    def block_time_in_seconds(self):
        if self._difficulty is None:
            return None

        best_hashrate = CryptoInfoEntityManager.instance().get_best_hashrate(self.cryptocurrency_name)
        return (self._difficulty * self._diff_multiplier) / best_hashrate

    @property
    def difficulty_block_progress(self):
        if self.state is None:
            return None

        return int(self.state % self._difficulty_window)

    @property
    def difficulty_retarget_height(self):
        if self.state is None:
            return None

        return int(self.state + (self._difficulty_window - self.difficulty_block_progress))

    @property
    def difficulty_previous_target_height(self):
        if self.difficulty_retarget_height is None:
            return None

        return int(self.difficulty_retarget_height - 2016)

    @property
    def difficulty_retarget_seconds(self):
        if self.difficulty_retarget_height is None or self.block_time_in_seconds is None:
            return None

        return int((self.difficulty_retarget_height - self.state) * self.block_time_in_seconds)

    @property
    def difficulty_retarget_percent_change(self):
        if self.difficulty_retarget_seconds is None:
            return None

        last_diff_timestamp = CryptoInfoEntityManager.instance().get_block_time(self.cryptocurrency_name)
        if last_diff_timestamp is None:
            return None

        time_window_expected = (self._block_time_minutes * 60) * self._difficulty_window
        time_next_diff = int(int(time.time()) + self.difficulty_retarget_seconds)
        time_window_current_diff = time_next_diff - last_diff_timestamp
        actual_percent_change = (((time_window_expected - time_window_current_diff) / time_window_current_diff) * 100)
        calc_percent_change = max([
            min([actual_percent_change, 300]),
            -75
        ])
        return round(calc_percent_change, 2)

    @property
    def difficulty_retarget_estimated_diff(self):
        if self.difficulty_retarget_percent_change is None:
            return None
        return round((self._difficulty * (1 + (self.difficulty_retarget_percent_change / 100))), 2)

    def hashrate_multiplier(self, unit_of_measurement):
        uom = unit_of_measurement.lower() if unit_of_measurement is not None else ""
        if uom.startswith("k"):
            return 1e3
        elif uom.startswith("m"):
            return 1e6
        elif uom.startswith("g"):
            return 1e9
        elif uom.startswith("t"):
            return 1e12
        elif uom.startswith("p"):
            return 1e15
        elif uom.startswith("e"):
            return 1e18
        elif uom.startswith("z"):
            return 1e21
        elif uom.startswith("y"):
            return 1e24
        elif uom.startswith("r"):
            return 1e27
        elif uom.startswith("q"):
            return 1e30
        else:
            return 1

    def hashrate_calc(self, unit_of_measurement):
        if self._hashrate is None:
            return None

        return round(float(self._hashrate) / self.hashrate_multiplier(unit_of_measurement), 4)

    @property
    def all_time_high_distance(self):
        if self._all_time_high is None or self.state is None:
            return None

        return round(float(self._all_time_high) - self.state, 2)

    @property
    def pool_control_1000b_perc(self):
        if self._pool_control_1000b is None:
            return None

        return round(((float(self._pool_control_1000b) / 1000.0) * 100.0), 4)

    def get_extra_state_attrs(self, full_attr_force=False):
        output_attrs = {
            ATTR_LAST_UPDATE: self._last_update,
        }

        if full_attr_force or self._fetch_type in CryptoInfoEntityManager.instance().fetch_price_types:
            output_attrs[ATTR_BASE_PRICE] = self._base_price
            output_attrs[ATTR_24H_VOLUME] = self._24h_volume
            output_attrs[ATTR_24H_CHANGE] = self._24h_change

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.PRICE_MAIN:
            output_attrs[ATTR_1H_CHANGE] = self._1h_change
            output_attrs[ATTR_7D_CHANGE] = self._7d_change
            output_attrs[ATTR_30D_CHANGE] = self._30d_change
            output_attrs[ATTR_CIRCULATING_SUPPLY] = self._circulating_supply
            output_attrs[ATTR_TOTAL_SUPPLY] = self._total_supply
            output_attrs[ATTR_ALL_TIME_HIGH] = self._all_time_high
            output_attrs[ATTR_ALL_TIME_LOW] = self._all_time_low
            output_attrs[ATTR_24H_LOW] = self._24h_low
            output_attrs[ATTR_24H_HIGH] = self._24h_high
            output_attrs[ATTR_IMAGE_URL] = self._image_url

        if full_attr_force or self._fetch_type in CryptoInfoEntityManager.instance().fetch_supply_types:
            output_attrs[ATTR_CIRCULATING_SUPPLY] = self._circulating_supply

        if full_attr_force or self._fetch_type in CryptoInfoEntityManager.instance().fetch_market_cap_types:
            output_attrs[ATTR_MARKET_CAP] = self._market_cap

        if full_attr_force or self._fetch_type in CryptoInfoEntityManager.instance().fetch_block_height_types:
            output_attrs[ATTR_BLOCK_HEIGHT] = self._block_height

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.CHAIN_SUMMARY:
            output_attrs[ATTR_DIFFICULTY] = self._difficulty
            output_attrs[ATTR_HASHRATE] = self._hashrate

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.CHAIN_CONTROL:
            output_attrs[ATTR_POOL_CONTROL_1000B] = self._pool_control_1000b

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.NOMP_POOL_STATS:
            output_attrs[ATTR_WORKER_COUNT] = self._worker_count
            output_attrs[ATTR_LAST_BLOCK] = self._last_block
            output_attrs[ATTR_BLOCKS_PENDING] = self._blocks_pending
            output_attrs[ATTR_BLOCKS_CONFIRMED] = self._blocks_confirmed
            output_attrs[ATTR_BLOCKS_ORPHANED] = self._blocks_orphaned

        return output_attrs

    @property
    def extra_state_attributes(self):
        return self.get_extra_state_attrs()

    def get_extra_sensor_attrs(self, full_attr_force=False, child_sensor=None):
        output_attrs = self.get_extra_state_attrs(full_attr_force=full_attr_force)

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.CHAIN_SUMMARY:

            if child_sensor is None or child_sensor.attribute_key == ATTR_BLOCK_TIME_IN_SECONDS:
                output_attrs[ATTR_BLOCK_TIME_IN_SECONDS] = self.block_time_in_seconds

            if child_sensor is None or child_sensor.attribute_key == ATTR_DIFFICULTY_BLOCK_PROGRESS:
                output_attrs[ATTR_DIFFICULTY_BLOCK_PROGRESS] = self.difficulty_block_progress

            if child_sensor is None or child_sensor.attribute_key == ATTR_DIFFICULTY_RETARGET_HEIGHT:
                output_attrs[ATTR_DIFFICULTY_RETARGET_HEIGHT] = self.difficulty_retarget_height

            if child_sensor is None or child_sensor.attribute_key == ATTR_DIFFICULTY_RETARGET_SECONDS:
                output_attrs[ATTR_DIFFICULTY_RETARGET_SECONDS] = self.difficulty_retarget_seconds

            if child_sensor is None or child_sensor.attribute_key == ATTR_DIFFICULTY_RETARGET_PERCENT_CHANGE:
                output_attrs[ATTR_DIFFICULTY_RETARGET_PERCENT_CHANGE] = self.difficulty_retarget_percent_change

            if child_sensor is None or child_sensor.attribute_key == ATTR_DIFFICULTY_RETARGET_ESTIMATED_DIFF:
                output_attrs[ATTR_DIFFICULTY_RETARGET_ESTIMATED_DIFF] = self.difficulty_retarget_estimated_diff

        if full_attr_force or self._fetch_type in CryptoInfoEntityManager.instance().fetch_hashrate_types:

            if child_sensor is None or child_sensor.attribute_key == ATTR_HASHRATE_CALC:
                output_attrs[ATTR_HASHRATE_CALC] = self.hashrate_calc(
                    child_sensor.unit_of_measurement if child_sensor is not None else None
                )

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.PRICE_MAIN:

            if child_sensor is None or child_sensor.attribute_key == ATTR_ALL_TIME_HIGH_DISTANCE:
                output_attrs[ATTR_ALL_TIME_HIGH_DISTANCE] = self.all_time_high_distance

        if full_attr_force or self._fetch_type == CryptoInfoDataFetchType.CHAIN_CONTROL:

            if child_sensor is None or child_sensor.attribute_key == ATTR_POOL_CONTROL_1000B_PERC:
                output_attrs[ATTR_POOL_CONTROL_1000B_PERC] = self.pool_control_1000b_perc

        return output_attrs

    @property
    def all_extra_sensor_keys(self):
        return self.get_extra_sensor_attrs(full_attr_force=True).keys()

    @classmethod
    def get_valid_extra_sensor_keys(cls):
        empty_sensor = CryptoinfoSensor(*["" for x in range(7)])
        keys = list(empty_sensor.all_extra_sensor_keys)
        del empty_sensor

        return keys

    @property
    def extra_sensor_attributes(self):
        return self.get_extra_sensor_attrs()

    @property
    def valid_attribute_keys(self):
        base_keys = list(self.extra_sensor_attributes.keys())

        return base_keys[:]

    def _build_name(self):
        if self._fetch_type not in CryptoInfoEntityManager.instance().fetch_price_types:
            return (
                SENSOR_PREFIX
                + (self._internal_id_name if len(self._internal_id_name) > 0 else (
                    (
                        self.cryptocurrency_name.upper()
                        if len(self.cryptocurrency_name) <= 6
                        else self.cryptocurrency_name.title()
                    )
                    + " " + self._fetch_type.name
                ))
            )

        else:
            return (
                SENSOR_PREFIX
                + (self._internal_id_name + " " if len(self._internal_id_name) > 0 else "")
                + self.cryptocurrency_name
                + " "
                + self.currency_name
            )

    @property
    def pool_prefix_id(self):
        return "".join(self.pool_prefixes)

    def _build_unique_id(self):
        if self._fetch_type not in CryptoInfoEntityManager.instance().fetch_price_types:
            if self._fetch_type == CryptoInfoDataFetchType.CHAIN_CONTROL:
                id_slug = f"{self._fetch_type.id_slug}_{self.pool_prefix_id}"
            else:
                id_slug = f"{self._fetch_type.id_slug}"
            return "{0}{1}{2}_{3}".format(
                self.cryptocurrency_name, self.multiplier, self._update_frequency, id_slug,
            )

        else:
            return "{0}{1}{2}{3}".format(
                self.cryptocurrency_name, self.currency_name, self.multiplier, self._update_frequency
            )

    def _build_device_class(self):
        if self._fetch_type in CryptoInfoEntityManager.instance().fetch_price_types:
            return SensorDeviceClass.MONETARY

        elif self._fetch_type in CryptoInfoEntityManager.instance().fetch_time_types:
            return SensorDeviceClass.DURATION

        else:
            return None

    def check_valid_config(self, raise_error=True):
        if self._fetch_type == CryptoInfoDataFetchType.NOMP_POOL_STATS:

            if self._api_domain_name is None:
                _LOGGER.error(f"No API domain name supplied for sensor {self.name}")

                if raise_error:
                    raise ValueError()

                return False

            if self._pool_name is None:
                _LOGGER.error(f"No pool name supplied for sensor {self.name}")

                if raise_error:
                    raise ValueError()

                return False

        return True

    def _log_api_error(self, error, r, tb):
        _LOGGER.error(
            "Cryptoinfo error fetching update: "
            + f"{type(error).__name__}: {error}"
            + " - response status: "
            + str(r.status_code if r is not None else None)
            + " - "
            + str(r.reason if r is not None else None)
        )
        _LOGGER.error(tb)

    def _api_fetch(self, api_data, url, extract_data, extract_primary):
        r = None
        try:
            if api_data is None:
                _LOGGER.warning(f"Fetching data for {self.name}")
                r = requests.get(url=url)
                api_data = extract_data(r.json())

            primary_data = extract_primary(api_data)
            self.data = api_data

        except Exception as error:
            tb = traceback.format_exc()
            self._log_api_error(error, r, tb)
            primary_data, api_data = None, None

        return primary_data, api_data

    def _extract_data_price_main_primary(self, api_data):
        return api_data["current_price"] * float(self.multiplier)

    def _extract_data_price_main_full(self, json_data):
        return json_data[0]

    def _extract_data_price_simple_primary(self, api_data):
        return api_data[self.currency_name] * float(self.multiplier)

    def _extract_data_price_simple_full(self, json_data):
        return json_data[self.cryptocurrency_name]

    def _extract_data_dominance_primary(self, api_data):
        return float(api_data["market_cap_percentage"][self.cryptocurrency_name])

    def _extract_data_dominance_full(self, json_data):
        return json_data["data"]

    def _extract_data_chain_summary_primary(self, api_data):
        return api_data[self.cryptocurrency_name]["height"]

    def _extract_data_chain_summary_full(self, json_data):
        return json_data

    def _extract_data_chain_control_primary(self, api_data):
        return True

    def _extract_data_chain_control_special(self, json_data):
        pool_data = None
        data_100_blk = 0
        data_1000_blk = 0
        for pool_prefix in self.pool_prefixes:
            if pool_prefix is not None and len(pool_prefix):
                for pool in json_data["pools"]:
                    if pool["name"].lower().startswith(pool_prefix.lower()):
                        pool_data = pool
                        data_100_blk += pool["nb100"]
                        data_1000_blk += pool["nb1000"]

        if pool_data is not None:
            return {
                **pool_data,
                "nb100": data_100_blk,
                "nb1000": data_1000_blk,
            }

        return None

    def _extract_data_chain_control_full(self, json_data):
        if self._extract_data_chain_control_special(json_data) is None:
            raise ValueError(f"Pool Prefixes {self.pool_prefixes} not found")

        return json_data

    def _extract_data_chain_orphans_primary(self, api_data):
        orphans_start_timestamp = api_data["d"] * DAY_SECONDS
        last_orphan_timestamp = (len(api_data["n"]) * DAY_SECONDS) + orphans_start_timestamp
        last_orphan_date = datetime.fromtimestamp(last_orphan_timestamp).date()
        today_date = datetime.now().date()
        orphans_today = api_data["n"][-1] if today_date == last_orphan_date else 0
        return orphans_today

    def _extract_data_chain_orphans_full(self, json_data):
        return json_data

    def _extract_data_chain_block_time_primary(self, api_data):
        return int(api_data)

    def _extract_data_chain_block_time_full(self, json_data):
        return json_data

    def _extract_data_nomp_pool_stats_full(self, json_data):
        pool_data = {
            **json_data["pools"][self._pool_name],
            **json_data["pools"][self._pool_name]["poolStats"],
            "blocks_pending": json_data["pools"][self._pool_name]["blocks"]["pending"],
            "blocks_confirmed": json_data["pools"][self._pool_name]["blocks"]["confirmed"],
            "blocks_orphaned": json_data["pools"][self._pool_name]["blocks"]["orphaned"],
        }

        for k in ["blocks", "workers", "poolFees", "poolStats"]:
            del pool_data[k]

        return pool_data

    def _extract_data_nomp_pool_stats_primary(self, api_data):
        return float(api_data["hashrate"])

    def _fetch_price_data_main(self, api_data=None):
        if not self._fetch_type == CryptoInfoDataFetchType.PRICE_MAIN:
            raise ValueError()

        price_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_PRICE_MAIN.format(API_BASE_URL_COINGECKO, self.cryptocurrency_name, self.currency_name),
            self._extract_data_price_main_full, self._extract_data_price_main_primary
        )

        if price_data is not None:
            self._update_all_properties(
                state=float(price_data),
                base_price=api_data["current_price"],
                volume_24h=api_data["total_volume"],
                change_1h=api_data["price_change_percentage_1h_in_currency"],
                change_24h=api_data["price_change_percentage_24h_in_currency"],
                change_7d=api_data["price_change_percentage_7d_in_currency"],
                change_30d=api_data["price_change_percentage_30d_in_currency"],
                market_cap=api_data["market_cap"],
                circulating_supply=api_data["circulating_supply"],
                total_supply=api_data["total_supply"],
                all_time_high=api_data["ath"],
                all_time_low=api_data["atl"],
                low_24h=api_data["low_24h"],
                high_24h=api_data["high_24h"],
                image_url=api_data["image"],
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_price_data_alternate(self, api_data=None):
        if self._fetch_type not in CryptoInfoEntityManager.instance().fetch_price_types:
            raise ValueError()

        price_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_PRICE_ALT.format(API_BASE_URL_COINGECKO, self.cryptocurrency_name, self.currency_name),
            self._extract_data_price_simple_full, self._extract_data_price_simple_primary
        )

        if price_data is not None:
            self._update_all_properties(
                state=float(price_data),
                base_price=api_data[self.currency_name],
                volume_24h=api_data[self.currency_name + "_24h_vol"],
                change_24h=api_data[self.currency_name + "_24h_change"],
                market_cap=api_data[self.currency_name + "_market_cap"]
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_dominance(self, api_data=None):
        dominance_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_DOMINANCE.format(API_BASE_URL_COINGECKO),
            self._extract_data_dominance_full,
            self._extract_data_dominance_primary
        )

        if dominance_data is not None:
            self._update_all_properties(
                state=round(dominance_data, 1),
                market_cap=api_data["total_market_cap"][self.cryptocurrency_name]
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_chain_summary(self, api_data=None):
        summary_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_CHAIN_SUMMARY.format(API_BASE_URL_CRYPTOID),
            self._extract_data_chain_summary_full,
            self._extract_data_chain_summary_primary
        )

        if summary_data is not None:
            self._update_all_properties(
                state=int(summary_data),
                difficulty=api_data[self.cryptocurrency_name]["diff"],
                circulating_supply=api_data[self.cryptocurrency_name]["supply"],
                hashrate=api_data[self.cryptocurrency_name]["hashrate"],
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_chain_control(self, api_data=None):
        control_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_CHAIN_CONTROL.format(API_BASE_URL_CRYPTOID, self.cryptocurrency_name),
            self._extract_data_chain_control_full,
            self._extract_data_chain_control_primary
        )

        if control_data is not None:
            pool_data = self._extract_data_chain_control_special(api_data)
            self._update_all_properties(
                state=int(pool_data["nb100"]),
                pool_control_1000b=pool_data["nb1000"],
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_chain_orphans(self, api_data=None):
        orphans_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_CHAIN_ORPHANS.format(API_BASE_URL_CRYPTOID, self.cryptocurrency_name),
            self._extract_data_chain_orphans_full,
            self._extract_data_chain_orphans_primary
        )

        if orphans_data is not None:
            self._update_all_properties(
                state=int(orphans_data),
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_chain_block_time(self, api_data=None):
        (block_height_arg, ) = self._get_fetch_args()

        try:
            block_height = int(block_height_arg)
        except Exception:
            block_height = CryptoInfoEntityManager.instance().get_last_diff(self.cryptocurrency_name)

            if block_height_arg is not None:
                _LOGGER.error("Error fetching " + self.name + " - Invalid block height arg supplied.")
            elif block_height is None:
                _LOGGER.error("Error fetching " + self.name + " - No data from Chain Summary sensor.")

        if block_height is None:
            raise ValueError()

        if self._state is not None and self._state > 0 and self._block_height == block_height:
            api_data = self._state

        block_time_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_CHAIN_BLOCK_TIME.format(API_BASE_URL_CRYPTOID, self.cryptocurrency_name, block_height),
            self._extract_data_chain_block_time_full,
            self._extract_data_chain_block_time_primary
        )

        if block_time_data is not None:
            self._update_all_properties(
                state=int(block_time_data),
                block_height=block_height,
            )

        else:
            raise ValueError()

        return self.data

    def _fetch_nomp_pool_stats(self, api_data=None):
        self.check_valid_config()

        hashrate_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_NOMP_POOL_STATS.format(self._api_domain_name),
            self._extract_data_nomp_pool_stats_full,
            self._extract_data_nomp_pool_stats_primary
        )

        if hashrate_data is not None:
            self._update_all_properties(
                state=float(hashrate_data),
                hashrate=float(hashrate_data),
                block_height=int(api_data["height"]),
                worker_count=int(api_data["workerCount"]),
                last_block=int(api_data["lastBlock"]),
                blocks_pending=int(api_data["blocks_pending"]),
                blocks_confirmed=int(api_data["blocks_confirmed"]),
                blocks_orphaned=int(api_data["blocks_orphaned"]),
            )

        else:
            raise ValueError()

        return self.data

    def _render_fetch_args(self):
        if self._fetch_args is None:
            return None

        args = self._fetch_args

        if "{" not in args:
            return args

        else:
            args_compiled = Template(args, self.hass)

        if args_compiled:
            try:
                args_to_render = {"arguments": args}
                rendered_args = args_compiled.render(args_to_render)
            except TemplateError as ex:
                _LOGGER.exception("Error rendering args template: %s", ex)
                return

        else:
            rendered_args = None

        if rendered_args == args:
            # No template used. default behavior
            pass

        else:
            # Template used. Construct the string used in the shell
            args = f"{rendered_args}"

        return args

    def _get_fetch_args(self, min_length=1, expected_length=1, default_value=None):
        rendered_args = self._render_fetch_args()

        if rendered_args is None or not len(rendered_args):
            return (None for x in range(expected_length))

        split_args = rendered_args.split(" ")
        args_len = len(split_args)

        if not args_len >= min_length:
            return (None for x in range(expected_length))

        if args_len < expected_length:
            split_args.extend([default_value for x in range(expected_length - args_len)])

        return (arg.strip() for arg in split_args[:expected_length])

    def _update_all_properties(
        self,
        state=None,
        base_price=None,
        volume_24h=None,
        change_1h=None,
        change_24h=None,
        change_7d=None,
        change_30d=None,
        market_cap=None,
        circulating_supply=None,
        total_supply=None,
        all_time_high=None,
        all_time_low=None,
        low_24h=None,
        high_24h=None,
        image_url=None,
        difficulty=None,
        hashrate=None,
        pool_control_1000b=None,
        block_height=None,
        worker_count=None,
        last_block=None,
        blocks_pending=None,
        blocks_confirmed=None,
        blocks_orphaned=None,
        available=True,
    ):
        self._state = state
        self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
        self._base_price = base_price
        self._24h_volume = volume_24h
        self._1h_change = change_1h
        self._24h_change = change_24h
        self._7d_change = change_7d
        self._30d_change = change_30d
        self._market_cap = market_cap
        self._circulating_supply = circulating_supply
        self._total_supply = total_supply
        self._all_time_high = all_time_high
        self._all_time_low = all_time_low
        self._24h_low = low_24h
        self._24h_high = high_24h
        self._difficulty = difficulty
        self._hashrate = hashrate
        self._pool_control_1000b = pool_control_1000b
        self._block_height = block_height
        self._worker_count = worker_count
        self._last_block = last_block
        self._blocks_pending = blocks_pending
        self._blocks_confirmed = blocks_confirmed
        self._blocks_orphaned = blocks_orphaned
        self._attr_available = available

        self._update_child_sensors()

    def get_child_data(self, child_sensor):
        child_data = self.get_extra_sensor_attrs(
            child_sensor=child_sensor
        )

        return child_data.get(child_sensor.attribute_key)

    def _update_child_sensors(self):
        if not len(self._child_sensors) > 0:
            return

        for sensor in self._child_sensors:
            sensor._update()

    def _get_child_sensors(self):
        child_sensors = list()

        if self._child_sensor_config is None or not len(self._child_sensor_config):
            return child_sensors

        valid_child_conf = list([
            conf for conf in self._child_sensor_config
            if conf[CONF_EXTRA_SENSOR_PROPERTY] in self.valid_attribute_keys
        ])

        for conf in valid_child_conf:
            id_name = conf.get(CONF_ID)
            unique_id = conf.get(CONF_UNIQUE_ID)
            state_class = conf.get(CONF_STATE_CLASS)
            attribute_key = conf.get(CONF_EXTRA_SENSOR_PROPERTY)
            unit_of_measurement = conf.get(CONF_UNIT_OF_MEASUREMENT)
            child_sensors.append(
                CryptoinfoChildSensor(
                    self,
                    id_name,
                    unique_id,
                    state_class,
                    attribute_key,
                    unit_of_measurement,
                )
            )

        self._child_sensors.extend(child_sensors)

        return child_sensors

    def _update(self):
        api_data = None

        if not CryptoInfoEntityManager.instance().should_fetch_entity(self):
            api_data = CryptoInfoEntityManager.instance().fetch_cached_entity_data(self)

        try:
            if self._fetch_type == CryptoInfoDataFetchType.DOMINANCE:
                api_data = self._fetch_dominance(api_data)

            elif self._fetch_type == CryptoInfoDataFetchType.CHAIN_SUMMARY:
                api_data = self._fetch_chain_summary(api_data)

            elif self._fetch_type == CryptoInfoDataFetchType.CHAIN_CONTROL:
                api_data = self._fetch_chain_control(api_data)

            elif self._fetch_type == CryptoInfoDataFetchType.CHAIN_ORPHANS:
                api_data = self._fetch_chain_orphans(api_data)

            elif self._fetch_type == CryptoInfoDataFetchType.CHAIN_BLOCK_TIME:
                api_data = self._fetch_chain_block_time(api_data)

            elif self._fetch_type == CryptoInfoDataFetchType.NOMP_POOL_STATS:
                api_data = self._fetch_nomp_pool_stats(api_data)

            else:
                api_data = self._fetch_price_data_main(api_data)

        except ValueError:
            try:
                api_data = self._fetch_price_data_alternate(api_data)
            except ValueError:
                self._update_all_properties(available=False)
                return

        CryptoInfoEntityManager.instance().set_cached_entity_data(self, api_data)


class CryptoinfoChildSensor(CryptoinfoSensor):
    def __init__(
        self,
        parent_sensor,
        id_name,
        unique_id,
        state_class,
        attribute_key,
        unit_of_measurement,
        *args,
        **kwargs
    ):
        super().__init__(
            hass=parent_sensor.hass,
            cryptocurrency_name=parent_sensor.cryptocurrency_name,
            currency_name=parent_sensor.currency_name,
            unit_of_measurement=unit_of_measurement,
            multiplier=parent_sensor.multiplier,
            update_frequency=parent_sensor._update_frequency,
            id_name=id_name,
            unique_id=unique_id,
            state_class=state_class,
            api_mode=CryptoInfoEntityManager.instance().get_extra_sensor_fetch_type_from_str(parent_sensor, attribute_key),
            pool_prefix=parent_sensor.pool_prefixes,
            fetch_args=parent_sensor._fetch_args,
            extra_sensors="",
            api_domain_name="",
            pool_name=parent_sensor._pool_name,
            is_child_sensor=True,
        )

        self._parent_sensor = parent_sensor
        self._attribute_key = attribute_key

    @property
    def attribute_key(self):
        return self._attribute_key

    def _update(self):
        new_state = self._parent_sensor.get_child_data(self)

        if new_state is not None and new_state != self._state:
            self._update_all_properties(state=new_state)

        elif new_state is None:
            self._update_all_properties(available=False)
