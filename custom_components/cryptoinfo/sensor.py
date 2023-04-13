#!/usr/bin/env python3
"""
Sensor component for Cryptoinfo
Author: Johnny Visser
"""

import requests
import voluptuous as vol
from datetime import datetime, timedelta
import urllib.error

from .const.const import (
    _LOGGER,
    CONF_CRYPTOCURRENCY_NAME,
    CONF_CURRENCY_NAME,
    CONF_MULTIPLIER,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_UPDATE_FREQUENCY,
    CONF_API_MODE,
    CONF_POOL_PREFIX,
    CONF_FETCH_ARGS,
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
    ATTR_ALL_TIME_LOW,
    ATTR_24H_LOW,
    ATTR_24H_HIGH,
    ATTR_IMAGE_URL,
    ATTR_DIFFICULTY,
    ATTR_HASHRATE,
    ATTR_POOL_CONTROL_1000B,
    ATTR_BLOCK_HEIGHT,
    API_BASE_URL_COINGECKO,
    API_BASE_URL_CRYPTOID,
    API_ENDPOINT_PRICE_MAIN,
    API_ENDPOINT_PRICE_ALT,
    API_ENDPOINT_DOMINANCE,
    API_ENDPOINT_CHAIN_SUMMARY,
    API_ENDPOINT_CHAIN_CONTROL,
    API_ENDPOINT_CHAIN_ORPHANS,
    API_ENDPOINT_CHAIN_BLOCK_TIME,
    CONF_ID,
    DAY_SECONDS,
)

from .manager import CryptoInfoEntityManager, CryptoInfoDataFetchType

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorDeviceClass
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CRYPTOCURRENCY_NAME, default="bitcoin"): cv.string,
        vol.Required(CONF_CURRENCY_NAME, default="usd"): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default="$"): cv.string,
        vol.Required(CONF_MULTIPLIER, default=1): cv.string,
        vol.Required(CONF_UPDATE_FREQUENCY, default=60): cv.string,
        vol.Optional(CONF_ID, default=""): cv.string,
        vol.Optional(
            CONF_API_MODE,
            default=str(CryptoInfoDataFetchType.PRICE_MAIN)
        ): vol.In(CryptoInfoEntityManager.instance().fetch_types),
        vol.Optional(CONF_POOL_PREFIX, default=""): cv.string,
        vol.Optional(CONF_FETCH_ARGS, default=""): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup Cryptoinfo sensor")

    id_name = config.get(CONF_ID)
    cryptocurrency_name = config.get(CONF_CRYPTOCURRENCY_NAME).lower().strip()
    currency_name = config.get(CONF_CURRENCY_NAME).strip()
    unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT).strip()
    multiplier = config.get(CONF_MULTIPLIER).strip()
    update_frequency = timedelta(minutes=(float(config.get(CONF_UPDATE_FREQUENCY))))
    api_mode = config.get(CONF_API_MODE)
    pool_prefix = config.get(CONF_POOL_PREFIX)
    fetch_args = config.get(CONF_FETCH_ARGS)

    entities = []

    try:
        entities.append(
            CryptoinfoSensor(
                hass,
                cryptocurrency_name,
                currency_name,
                unit_of_measurement,
                multiplier,
                update_frequency,
                id_name,
                api_mode,
                pool_prefix,
                fetch_args,
            )
        )
    except urllib.error.HTTPError as error:
        _LOGGER.error(error.reason)
        return False

    add_entities(entities)
    CryptoInfoEntityManager.instance().add_entities(entities)


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
        api_mode,
        pool_prefix,
        fetch_args,
    ):
        self.hass = hass
        self._fetch_type = CryptoInfoEntityManager.instance().get_fetch_type_from_str(api_mode)
        self._update_frequency = update_frequency
        self._fetch_args = fetch_args if fetch_args and len(fetch_args) else None
        self.data = None
        self.cryptocurrency_name = cryptocurrency_name
        self.currency_name = currency_name
        self.pool_prefix = pool_prefix
        self._unit_of_measurement = unit_of_measurement
        self.multiplier = multiplier
        self.update = Throttle(update_frequency)(self._update)
        if self._fetch_type in CryptoInfoEntityManager.instance().fetch_price_types:
            self._attr_device_class = SensorDeviceClass.MONETARY
        elif self._fetch_type in CryptoInfoEntityManager.instance().fetch_time_types:
            self._attr_device_class = SensorDeviceClass.DURATION
        else:
            self._attr_device_class = None
        if self._fetch_type not in CryptoInfoEntityManager.instance().fetch_price_types:
            self._name = (
                SENSOR_PREFIX
                + (id_name if len(id_name) > 0 else (
                    cryptocurrency_name.upper()
                    + " " + self._fetch_type.name
                ))
            )
        else:
            self._name = (
                SENSOR_PREFIX
                + (id_name + " " if len(id_name) > 0 else "")
                + cryptocurrency_name
                + " "
                + currency_name
            )
        self._icon = "mdi:bitcoin"
        self._state = None
        self._last_update = None
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
        self._state_class = "measurement"
        if self._fetch_type not in CryptoInfoEntityManager.instance().fetch_price_types:
            self._attr_unique_id = (
                cryptocurrency_name
                + str(multiplier)
                + str(update_frequency)
                + "_" + self._fetch_type.id_slug
            )
        else:
            self._attr_unique_id = (
                cryptocurrency_name
                + currency_name
                + str(multiplier)
                + str(update_frequency)
            )
        self._attr_available = True

    @property
    def update_frequency(self):
        return self._update_frequency

    @property
    def fetch_type(self):
        return self._fetch_type

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
        return self._state_class

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        base_attrs = {
            ATTR_LAST_UPDATE: self._last_update,
        }
        extra_attrs = {
            ATTR_MARKET_CAP: self._market_cap,
        }
        if self._fetch_type == CryptoInfoDataFetchType.CHAIN_ORPHANS:
            return {**base_attrs}
        if self._fetch_type == CryptoInfoDataFetchType.CHAIN_BLOCK_TIME:
            return {
                **base_attrs,
                ATTR_BLOCK_HEIGHT: self._block_height
            }
        if self._fetch_type == CryptoInfoDataFetchType.DOMINANCE:
            return {**base_attrs, **extra_attrs}
        if self._fetch_type == CryptoInfoDataFetchType.CHAIN_SUMMARY:
            return {
                **base_attrs,
                ATTR_DIFFICULTY: self._difficulty,
                ATTR_HASHRATE: self._hashrate,
                ATTR_CIRCULATING_SUPPLY: self._circulating_supply,
            }
        if self._fetch_type == CryptoInfoDataFetchType.CHAIN_CONTROL:
            return {
                **base_attrs,
                ATTR_POOL_CONTROL_1000B: self._pool_control_1000b,
            }
        simple_attrs = {
            ATTR_BASE_PRICE: self._base_price,
            ATTR_24H_VOLUME: self._24h_volume,
            ATTR_24H_CHANGE: self._24h_change,
        }
        if self._fetch_type == CryptoInfoDataFetchType.PRICE_SIMPLE:
            return {
                **base_attrs,
                **extra_attrs,
                **simple_attrs
            }
        return {
            **base_attrs,
            **extra_attrs,
            **simple_attrs,
            ATTR_1H_CHANGE: self._1h_change,
            ATTR_7D_CHANGE: self._7d_change,
            ATTR_30D_CHANGE: self._30d_change,
            ATTR_CIRCULATING_SUPPLY: self._circulating_supply,
            ATTR_TOTAL_SUPPLY: self._total_supply,
            ATTR_ALL_TIME_HIGH: self._all_time_high,
            ATTR_ALL_TIME_LOW: self._all_time_low,
            ATTR_24H_LOW: self._24h_low,
            ATTR_24H_HIGH: self._24h_high,
            ATTR_IMAGE_URL: self._image_url,
        }

    def _log_api_error(self, error, r):
        _LOGGER.error(
            "Error fetching update from coingecko: "
            + str(error)
            + " - response status: "
            + str(r.status_code if r is not None else None)
            + " - "
            + str(r.reason if r is not None else None)
        )

    def _api_fetch(self, api_data, url, extract_data, extract_primary):
        r = None
        try:
            if api_data is None:
                r = requests.get(url=url)
                api_data = extract_data(r.json())
            primary_data = extract_primary(api_data)
            self.data = api_data
        except Exception as error:
            self._log_api_error(error, r)
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
        return api_data["market_cap_percentage"][self.cryptocurrency_name]

    def _extract_data_dominance_full(self, json_data):
        return json_data["data"]

    def _extract_data_chain_summary_primary(self, api_data):
        return api_data[self.cryptocurrency_name]["height"]

    def _extract_data_chain_summary_full(self, json_data):
        return json_data

    def _extract_data_chain_control_primary(self, api_data):
        return api_data["nb100"]

    def _extract_data_chain_control_full(self, json_data):
        for pool in json_data["pools"]:
            if pool["name"].startswith(self.pool_prefix):
                return pool
        raise ValueError("Pool Prefix not found")

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
                state=float(dominance_data),
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
            self._update_all_properties(
                state=int(control_data),
                pool_control_1000b=api_data["nb1000"],
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
        (block_height, ) = self._get_fetch_args()
        if block_height is None:
            _LOGGER.error("Error fetching " + self.name + " - No args supplied.")
            raise ValueError()
        try:
            block_height = int(block_height)
        except Exception:
            _LOGGER.error("Error fetching " + self.name + " - Invalid block height supplied.")
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
        self._attr_available = available

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
            else:
                api_data = self._fetch_price_data_main(api_data)
        except ValueError:
            try:
                api_data = self._fetch_price_data_alternate(api_data)
            except ValueError:
                self._update_all_properties(available=False)
                return
        CryptoInfoEntityManager.instance().set_cached_entity_data(self, api_data)
