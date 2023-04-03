import logging

CONF_ID = "id"
CONF_CRYPTOCURRENCY_NAME = "cryptocurrency_name"
CONF_CURRENCY_NAME = "currency_name"
CONF_MULTIPLIER = "multiplier"
CONF_UPDATE_FREQUENCY = "update_frequency"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_USE_SIMPLE_PRICE = "use_simple_price"
CONF_IS_DOMINANCE_SENSOR = "is_dominance_sensor"

SENSOR_PREFIX = "Cryptoinfo "
ATTR_LAST_UPDATE = "last_update"
ATTR_BASE_PRICE = "baseprice"
ATTR_24H_VOLUME = "24h_volume"
ATTR_1H_CHANGE = "1h_change"
ATTR_24H_CHANGE = "24h_change"
ATTR_7D_CHANGE = "7d_change"
ATTR_30D_CHANGE = "30d_change"
ATTR_MARKET_CAP = "market_cap"
ATTR_CIRCULATING_SUPPLY = "circulating_supply"
ATTR_TOTAL_SUPPLY = "total_supply"
ATTR_ALL_TIME_HIGH = "all_time_high"
ATTR_ALL_TIME_LOW = "all_time_low"
ATTR_24H_LOW = "24h_low"
ATTR_24H_HIGH = "24h_high"
ATTR_IMAGE_URL = "image_url"

API_BASE_URL = "https://api.coingecko.com/api/v3/"
API_ENDPOINT_MAIN = (
    "{0}coins/markets?ids={1}&vs_currency={2}"
    "&page=1&sparkline=false&price_change_percentage=1h%2C24h%2C7d%2C30d"
)
API_ENDPOINT_ALT = (
    "{0}simple/price?ids={1}&vs_currencies={2}"
    "&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"
)
API_ENDPOINT_DOM = "{0}global"

_LOGGER = logging.getLogger(__name__)
