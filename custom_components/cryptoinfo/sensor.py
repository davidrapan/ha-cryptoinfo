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
    CONF_IS_DOMINANCE_SENSOR,
    CONF_MULTIPLIER,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_UPDATE_FREQUENCY,
    CONF_USE_SIMPLE_PRICE,
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
    API_BASE_URL,
    API_ENDPOINT_MAIN,
    API_ENDPOINT_ALT,
    API_ENDPOINT_DOM,
    CONF_ID,
)

from .manager import CryptoInfoEntityManager, CryptoInfoDataFetchType

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorDeviceClass
import homeassistant.helpers.config_validation as cv
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
        vol.Optional(CONF_USE_SIMPLE_PRICE, default=False): cv.boolean,
        vol.Optional(CONF_IS_DOMINANCE_SENSOR, default=False): cv.boolean,
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
    use_simple_price = bool(config.get(CONF_USE_SIMPLE_PRICE))
    is_dominance_sensor = bool(config.get(CONF_IS_DOMINANCE_SENSOR))

    entities = []

    try:
        entities.append(
            CryptoinfoSensor(
                cryptocurrency_name,
                currency_name,
                unit_of_measurement,
                multiplier,
                update_frequency,
                id_name,
                use_simple_price,
                is_dominance_sensor,
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
        cryptocurrency_name,
        currency_name,
        unit_of_measurement,
        multiplier,
        update_frequency,
        id_name,
        use_simple_price,
        is_dominance_sensor,
    ):
        self._is_dominance_sensor = is_dominance_sensor
        self._fetch_type = CryptoInfoDataFetchType.PRICE_MAIN
        self._update_frequency = update_frequency
        self.data = None
        self.cryptocurrency_name = cryptocurrency_name
        self.currency_name = currency_name
        self._unit_of_measurement = unit_of_measurement
        self.multiplier = multiplier
        self.update = Throttle(update_frequency)(self._update)
        self._attr_device_class = SensorDeviceClass.MONETARY
        if not self._is_dominance_sensor:
            self._name = (
                SENSOR_PREFIX
                + (id_name + " " if len(id_name) > 0 else "")
                + cryptocurrency_name
                + " "
                + currency_name
            )
        else:
            self._name = (
                SENSOR_PREFIX
                + id_name if len(id_name) > 0 else (
                    cryptocurrency_name
                    + " Dominance"
                )
            )
            self._fetch_type = CryptoInfoDataFetchType.DOMINANCE
        self._use_simple_price = use_simple_price
        if self._use_simple_price:
            self._fetch_type = CryptoInfoDataFetchType.PRICE_SIMPLE
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
        self._state_class = "measurement"
        if not self._is_dominance_sensor:
            self._attr_unique_id = (
                cryptocurrency_name
                + currency_name
                + str(multiplier)
                + str(update_frequency)
            )
        else:
            self._attr_unique_id = (
                cryptocurrency_name
                + str(multiplier)
                + str(update_frequency)
                + "_dom"
            )

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
            ATTR_MARKET_CAP: self._market_cap,
        }
        if self._is_dominance_sensor:
            return base_attrs
        simple_attrs = {
            ATTR_BASE_PRICE: self._base_price,
            ATTR_24H_VOLUME: self._24h_volume,
            ATTR_24H_CHANGE: self._24h_change,
        }
        if self._use_simple_price:
            return {**base_attrs, **simple_attrs}
        return {
            **base_attrs,
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

    def _fetch_price_data_main(self, api_data=None):
        if self._use_simple_price or self._is_dominance_sensor:
            raise ValueError()
        price_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_MAIN.format(API_BASE_URL, self.cryptocurrency_name, self.currency_name),
            self._extract_data_price_main_full, self._extract_data_price_main_primary
        )
        if price_data:
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
        if self._is_dominance_sensor:
            raise ValueError()
        price_data, api_data = self._api_fetch(
            api_data,
            API_ENDPOINT_ALT.format(API_BASE_URL, self.cryptocurrency_name, self.currency_name),
            self._extract_data_price_simple_full, self._extract_data_price_simple_primary
        )
        if price_data:
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
            API_ENDPOINT_DOM.format(API_BASE_URL),
            self._extract_data_dominance_full,
            self._extract_data_dominance_primary
        )
        if dominance_data:
            self._update_all_properties(
                state=float(dominance_data),
                market_cap=api_data["total_market_cap"][self.cryptocurrency_name]
            )
        else:
            raise ValueError()
        return self.data

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
        self._image_url = image_url

    def _update(self):
        api_data = None
        if not CryptoInfoEntityManager.instance().should_fetch_entity(self):
            api_data = CryptoInfoEntityManager.instance().fetch_cached_entity_data(self)
        try:
            if self._is_dominance_sensor:
                api_data = self._fetch_dominance(api_data)
            else:
                api_data = self._fetch_price_data_main(api_data)
        except ValueError:
            try:
                api_data = self._fetch_price_data_alternate(api_data)
            except ValueError:
                self._update_all_properties()
                return
        CryptoInfoEntityManager.instance().set_cached_entity_data(self, api_data)
