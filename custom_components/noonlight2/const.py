from homeassistant.const import Platform
from noonlight import (
    NOONLIGHT_SERVICES_FIRE,
    NOONLIGHT_SERVICES_MEDICAL,
    NOONLIGHT_SERVICES_POLICE,
)

VERSION = "v2.0.1"
DOMAIN = "noonlight2"

PLATFORMS = [Platform.SWITCH]

DEFAULT_NAME = "Noonlight2"
DEFAULT_API_ENDPOINT = "https://api.noonlight.com/dispatch/v1"

CONF_SERVER_TOKEN = "server_token"
CONF_API_ENDPOINT = "api_endpoint"
CONF_PHONE_NUMBER = "phone_number"
CONF_ADDRESS_LINE1 = "address1"
CONF_ADDRESS_LINE2 = "address2"
CONF_CITY = "city"
CONF_STATE = "state"
CONF_ZIP = "zip"
CONF_COUNTRY = "country"
CONF_LOCATION_MODE = "location_mode"

CONST_ALARM_STATUS_ACTIVE = "ACTIVE"
CONST_ALARM_STATUS_CANCELED = "CANCELED"
CONST_NOONLIGHT_HA_SERVICE_CREATE_ALARM = "create_alarm"

CONST_NOONLIGHT_SERVICE_TYPES = (
    NOONLIGHT_SERVICES_POLICE,
    NOONLIGHT_SERVICES_FIRE,
    NOONLIGHT_SERVICES_MEDICAL,
)

EVENT_NOONLIGHT_TOKEN_REFRESHED = "noonlight2_token_refreshed"
EVENT_NOONLIGHT_ALARM_CANCELED = "noonlight2_alarm_canceled"
EVENT_NOONLIGHT_ALARM_CREATED = "noonlight2_alarm_created"

NOTIFICATION_TOKEN_UPDATE_FAILURE = "noonlight2_token_update_failure"
NOTIFICATION_TOKEN_UPDATE_SUCCESS = "noonlight2_token_update_success"
NOTIFICATION_ALARM_CREATE_FAILURE = "noonlight2_alarm_create_failure"
