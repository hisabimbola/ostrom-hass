"""Constants for the Ostrom integration."""
DOMAIN = "ostrom-hass"

DEFAULT_NAME = "Ostrom"
CONF_API_KEY = "api_key"
CONF_ZIP_CODE = "zip_code"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# Base URLs for the Ostrom API
BASE_URL = "https://production.ostrom-api.io"
AUTH_URL = "https://auth.production.ostrom-api.io/oauth2/token"

# Default client credentials
DEFAULT_CLIENT_ID = "1c4fcc73d1d89e998d69307ea0ad5fe"
DEFAULT_CLIENT_SECRET = "514ac2b67536a71513481a38a823d3d013a94e21e17ecaeae41caee8c366139"

# Update interval in seconds (5 minutes)
UPDATE_INTERVAL = 300

# Token refresh interval in seconds (50 minutes)
TOKEN_REFRESH_INTERVAL = 3000

# Device information
MANUFACTURER = "Ostrom"
MODEL = "Energy Price API"
ATTRIBUTION = "Data provided by Ostrom GmbH"

# Available sensors
SENSOR_TYPES = {
    "electricity_current_price": {
        "name": "Ostrom Electricity Current Price",
        "unit": "€/kWh",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_next_hour_price": {
        "name": "Ostrom Electricity Next Hour Price",
        "unit": "€/kWh",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_lowest_price_today": {
        "name": "Ostrom Electricity Lowest Price Today",
        "unit": "€/kWh",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_highest_price_today": {
        "name": "Ostrom Electricity Highest Price Today",
        "unit": "€/kWh",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_base_fee": {
        "name": "Ostrom Electricity Monthly Base Fee",
        "unit": "€",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_grid_fee": {
        "name": "Ostrom Electricity Monthly Grid Fee",
        "unit": "€",
        "icon": "mdi:currency-eur",
        "device_class": "monetary",
    },
    "electricity_prices_today": {
        "name": "Ostrom Electricity Prices Today",
        "unit": None,
        "icon": "mdi:chart-line",
        "device_class": None,
    }
}
