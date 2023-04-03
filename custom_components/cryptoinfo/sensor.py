#!/usr/bin/env python3
"""
Sensor component for Cryptoinfo
Author: Johnny Visser
"""

import requests
import voluptuous as vol
from datetime import datetime, date, timedelta
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
    API_ENDPOINT,
    CONF_ID,
)

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
        self._use_simple_price = use_simple_price
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

    def _fetch_price_data_main(self):
        if self._use_simple_price or self._is_dominance_sensor:
            raise ValueError()
        url = (
            API_ENDPOINT
            + "coins/markets?ids="
            + self.cryptocurrency_name
            + "&vs_currency="
            + self.currency_name
            + "&page=1&sparkline=false&price_change_percentage=1h%2C24h%2C7d%2C30d"
        )
        r = None
        try:
            # sending get request
            r = requests.get(url=url)
            # extracting response json
            self.data = r.json()[0]
            # multiply the price
            price_data = self.data["current_price"] * float(self.multiplier)
        except Exception as error:
            _LOGGER.error(
                "Error fetching update from coingecko: "
                + str(error)
                + " - response status: "
                + str(r.status_code if r is not None else None)
                + " - "
                + str(r.reason if r is not None else None)
            )
            price_data = None

        if price_data:
            # Set the values of the sensor
            self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
            self._state = float(price_data)
            # set the attributes of the sensor
            self._base_price = r.json()[0]["current_price"]
            self._24h_volume = r.json()[0]["total_volume"]
            self._1h_change = r.json()[0]["price_change_percentage_1h_in_currency"]
            self._24h_change = r.json()[0][
                "price_change_percentage_24h_in_currency"
            ]
            self._7d_change = r.json()[0]["price_change_percentage_7d_in_currency"]
            self._30d_change = r.json()[0][
                "price_change_percentage_30d_in_currency"
            ]
            self._market_cap = r.json()[0]["market_cap"]
            self._circulating_supply = r.json()[0]["circulating_supply"]
            self._total_supply = r.json()[0]["total_supply"]
            self._all_time_high = r.json()[0]["ath"]
            self._all_time_low = r.json()[0]["atl"]
            self._24h_low = r.json()[0]["low_24h"]
            self._24h_high = r.json()[0]["high_24h"]
            self._image_url = r.json()[0]["image"]
        else:
            raise ValueError()

    def _fetch_price_data_alternate(self):
        if self._is_dominance_sensor:
            raise ValueError()
        url = (
            API_ENDPOINT
            + "simple/price?ids="
            + self.cryptocurrency_name
            + "&vs_currencies="
            + self.currency_name
            + "&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"
        )
        r = None
        try:
            # sending get request
            r = requests.get(url=url)
            # extracting response json
            self.data = r.json()[self.cryptocurrency_name]
            # multiply the price
            price_data = self.data[self.currency_name] * float(self.multiplier)
        except Exception as error:
            _LOGGER.error(
                "Error fetching update from coingecko: "
                + str(error)
                + " - response status: "
                + str(r.status_code if r is not None else None)
                + " - "
                + str(r.reason if r is not None else None)
            )
            price_data = None

        if price_data:
            # Set the values of the sensor
            self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
            self._state = float(price_data)
            # set the attributes of the sensor
            self._base_price = r.json()[self.cryptocurrency_name][self.currency_name]
            self._24h_volume = r.json()[self.cryptocurrency_name][self.currency_name+ "_24h_vol"]
            self._1h_change = None
            self._24h_change = r.json()[self.cryptocurrency_name][self.currency_name+ "_24h_change"]
            self._7d_change = None
            self._30d_change = None
            self._market_cap = r.json()[self.cryptocurrency_name][self.currency_name+ "_market_cap"]
            self._circulating_supply = None
            self._total_supply = None
            self._all_time_high = None
            self._all_time_low = None
            self._24h_low = None
            self._24h_high = None
            self._image_url = None
        else:
            raise ValueError()

    def _fetch_dominance(self):
        url = (
            API_ENDPOINT
            + "global"
        )
        r = None
        try:
            # sending get request
            r = requests.get(url=url)
            # extracting response json
            self.data = r.json()["data"]
            # multiply the price
            dominance_data = self.data["market_cap_percentage"][self.cryptocurrency_name]
        except Exception as error:
            _LOGGER.error(
                "Error fetching update from coingecko: "
                + str(error)
                + " - response status: "
                + str(r.status_code if r is not None else None)
                + " - "
                + str(r.reason if r is not None else None)
            )
            dominance_data = None

        if dominance_data:
            # Set the values of the sensor
            self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
            self._state = float(dominance_data)
            # set the attributes of the sensor
            self._base_price = None
            self._24h_volume = None
            self._1h_change = None
            self._24h_change = None
            self._7d_change = None
            self._30d_change = None
            self._market_cap = self.data["total_market_cap"][self.cryptocurrency_name]
            self._circulating_supply = None
            self._total_supply = None
            self._all_time_high = None
            self._all_time_low = None
            self._24h_low = None
            self._24h_high = None
            self._image_url = None
        else:
            raise ValueError()

    def _update(self):
        try:
            if self._is_dominance_sensor:
                self._fetch_dominance()
            else:
                self._fetch_price_data_main()
        except ValueError:
            try:
                self._fetch_price_data_alternate()
            except ValueError:
                self._state = None
                self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
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
