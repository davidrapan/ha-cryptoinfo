#!/usr/bin/env python3
"""
Sensor component for Cryptoinfo
Author: Johnny Visser
"""

import voluptuous as vol
from datetime import timedelta
import urllib.error

from .const.const import (
    _LOGGER,
    CONF_CRYPTOCURRENCY_NAME,
    CONF_CURRENCY_NAME,
    CONF_MULTIPLIER,
    CONF_UPDATE_FREQUENCY,
    CONF_API_MODE,
    CONF_POOL_PREFIX,
    CONF_FETCH_ARGS,
    CONF_EXTRA_SENSORS,
    CONF_EXTRA_SENSOR_PROPERTY,
    CONF_API_DOMAIN_NAME,
    CONF_POOL_NAME,
    CONF_DIFF_MULTIPLIER,
    CONF_BLOCK_TIME_MINUTES,
    CONF_DIFFICULTY_WINDOW,
    CONF_HALVING_WINDOW,
)

from .manager import CryptoInfoEntityManager, CryptoInfoDataFetchType
from .crypto_sensor import CryptoinfoSensor

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    PLATFORM_SCHEMA,
    STATE_CLASSES_SCHEMA,
)
from homeassistant.const import (
    CONF_UNIQUE_ID,
    CONF_ID,
    CONF_UNIT_OF_MEASUREMENT,
)
import homeassistant.helpers.config_validation as cv


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup Cryptoinfo sensor")

    id_name = config.get(CONF_ID)
    unique_id = config.get(CONF_UNIQUE_ID)
    state_class = config.get(CONF_STATE_CLASS)
    cryptocurrency_name = config.get(CONF_CRYPTOCURRENCY_NAME).lower().strip()
    currency_name = config.get(CONF_CURRENCY_NAME).lower().strip()
    unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT).strip()
    multiplier = config.get(CONF_MULTIPLIER).strip()
    update_frequency = timedelta(minutes=(float(config.get(CONF_UPDATE_FREQUENCY))))
    api_mode = config.get(CONF_API_MODE).lower().strip()
    pool_prefix = config.get(CONF_POOL_PREFIX)
    fetch_args = config.get(CONF_FETCH_ARGS)
    extra_sensors = config.get(CONF_EXTRA_SENSORS, [])
    api_domain_name = config.get(CONF_API_DOMAIN_NAME).lower().strip()
    pool_name = config.get(CONF_POOL_NAME).strip()
    diff_multiplier = config.get(CONF_DIFF_MULTIPLIER)
    block_time_minutes = config.get(CONF_BLOCK_TIME_MINUTES)
    difficulty_window = config.get(CONF_DIFFICULTY_WINDOW)
    halving_window = config.get(CONF_HALVING_WINDOW)

    entities = []

    try:
        new_sensor = CryptoinfoSensor(
            hass,
            cryptocurrency_name,
            currency_name,
            unit_of_measurement,
            multiplier,
            update_frequency,
            id_name,
            unique_id,
            state_class,
            api_mode,
            pool_prefix,
            fetch_args,
            extra_sensors,
            api_domain_name,
            pool_name,
            diff_multiplier,
            block_time_minutes,
            difficulty_window,
            halving_window,
        )
        if new_sensor.check_valid_config(False):
            entities.append(new_sensor)
            entities.extend(new_sensor._get_child_sensors())
    except urllib.error.HTTPError as error:
        _LOGGER.error(error.reason)
        return False

    add_entities(entities)
    CryptoInfoEntityManager.instance().add_entities(entities)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CRYPTOCURRENCY_NAME, default="bitcoin"): cv.string,
        vol.Required(CONF_CURRENCY_NAME, default="usd"): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default="$"): cv.string,
        vol.Required(CONF_MULTIPLIER, default=1): cv.string,
        vol.Required(CONF_UPDATE_FREQUENCY, default=60): cv.string,
        vol.Optional(CONF_ID, default=""): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
        vol.Optional(
            CONF_API_MODE,
            default=str(CryptoInfoDataFetchType.PRICE_MAIN)
        ): vol.In(CryptoInfoEntityManager.instance().fetch_types),
        vol.Optional(CONF_POOL_PREFIX, default=[""]): vol.All(
            cv.ensure_list,
            [cv.string],
        ),
        vol.Optional(CONF_FETCH_ARGS, default=""): cv.string,
        vol.Optional(CONF_EXTRA_SENSORS): vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Optional(CONF_ID, default=""): cv.string,
                        vol.Optional(CONF_UNIQUE_ID): cv.string,
                        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
                        vol.Required(CONF_EXTRA_SENSOR_PROPERTY): vol.In(CryptoinfoSensor.get_valid_extra_sensor_keys()),
                        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default="$"): cv.string,
                    }
                )
            ],
        ),
        vol.Optional(CONF_API_DOMAIN_NAME, default=""): cv.string,
        vol.Optional(CONF_POOL_NAME, default=""): cv.string,
        vol.Optional(CONF_DIFF_MULTIPLIER, default=""): cv.string,
        vol.Optional(CONF_BLOCK_TIME_MINUTES, default=""): cv.string,
        vol.Optional(CONF_DIFFICULTY_WINDOW, default=""): cv.string,
        vol.Optional(CONF_HALVING_WINDOW, default=""): cv.string,
    }
)
