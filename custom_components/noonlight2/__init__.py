"""Noonlight integration for Home Assistant."""

import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_time_interval,
)
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType

import aiohttp
import json

from .const import (
    CONF_ADDRESS_LINE1,
    CONF_ADDRESS_LINE2,
    CONF_API_ENDPOINT,
    CONF_CITY,
    CONF_PHONE_NUMBER,
    CONF_SERVER_TOKEN,
    CONF_STATE,
    CONF_ZIP,
    CONF_COUNTRY,
    CONST_ALARM_STATUS_ACTIVE,
    CONST_ALARM_STATUS_CANCELED,
    CONST_NOONLIGHT_HA_SERVICE_CREATE_ALARM,
    DOMAIN,
    EVENT_NOONLIGHT_ALARM_CANCELED,
    EVENT_NOONLIGHT_ALARM_CREATED,
    EVENT_NOONLIGHT_TOKEN_REFRESHED,
    NOTIFICATION_ALARM_CREATE_FAILURE,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)
TOKEN_CHECK_INTERVAL = timedelta(minutes=15)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERVER_TOKEN): cv.string,
                vol.Required(CONF_API_ENDPOINT): cv.string,
                vol.Required(CONF_PHONE_NUMBER): cv.string,
                vol.Optional(CONF_ADDRESS_LINE1): cv.string,
                vol.Optional(CONF_ADDRESS_LINE2): cv.string,
                vol.Optional(CONF_CITY): cv.string,
                vol.Optional(CONF_STATE): cv.string,
                vol.Optional(CONF_ZIP): cv.string,
                vol.Optional(CONF_COUNTRY): cv.string,
                vol.Inclusive(
                    CONF_LATITUDE, "coordinates", "Include both latitude and longitude"
                ): cv.latitude,
                vol.Inclusive(
                    CONF_LONGITUDE, "coordinates", "Include both latitude and longitude"
                ): cv.longitude,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from YAML."""
    if DOMAIN not in config:
        return True

    _LOGGER.debug(f"[async_setup] config: {config[DOMAIN]}")
    async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        breaks_in_ha_version="2025.1",
        is_fixable=False,
        is_persistent=False,
        issue_domain=DOMAIN,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": "Noonlight2",
        },
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    _LOGGER.debug(f"[init async_setup_entry] entry: {entry.data}")
    noonlight_integration = NoonlightIntegration(hass, entry.data)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = noonlight_integration

    async def handle_create_alarm_service(call):
        """Create a noonlight alarm from a service"""
        service = call.data.get("service", None)
        await noonlight_integration.create_alarm(alarm_types=[service])

    hass.services.async_register(
        DOMAIN, CONST_NOONLIGHT_HA_SERVICE_CREATE_ALARM, handle_create_alarm_service
    )

    # Server token validation - no periodic renewal needed
    if not await noonlight_integration.check_api_token():
        _LOGGER.error("Noonlight server token is missing or invalid")
        return False

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"Unloading: {entry.data}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok


class NoonlightException(HomeAssistantError):
    """General exception for Noonlight Integration."""

    pass


class NoonlightIntegration:
    """Integration for interacting with Noonlight from Home Assistant."""

    def __init__(self, hass, conf):
        """Initialize NoonlightIntegration."""
        self.hass = hass
        self.config = conf
        self._alarm = None
        self._websession = async_get_clientsession(self.hass)
        self.api_endpoint = self.config[CONF_API_ENDPOINT]
        self.server_token = self.config[CONF_SERVER_TOKEN]

        # Add address portions, if exist
        self.addline1 = self.config.get(CONF_ADDRESS_LINE1, "")
        self.addline2 = self.config.get(CONF_ADDRESS_LINE2, "")
        self.addcity = self.config.get(CONF_CITY, "")
        self.addstate = self.config.get(CONF_STATE, "")
        self.addzip = self.config.get(CONF_ZIP, "")
        self.addcountry = self.config.get(CONF_COUNTRY, "")

    @property
    def latitude(self):
        """Return latitude from the Home Assistant configuration."""
        return self.config.get(CONF_LATITUDE, self.hass.config.latitude)

    @property
    def longitude(self):
        """Return longitude from the Home Assistant configuration."""
        return self.config.get(CONF_LONGITUDE, self.hass.config.longitude)

    @property
    def headers(self):
        """Return headers for Noonlight API requests."""
        return {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }

    async def check_api_token(self, force_renew=False):
        """Check if server token is valid."""
        # Server tokens don't expire, just verify the token is present
        return bool(self.server_token)

    async def update_alarm_status(self):
        """Update the status of the current alarm."""
        if self._alarm is not None:
            try:
                url = f"{self.api_endpoint}/alarms/{self._alarm['id']}/status"
                async with self._websession.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        alarm_data = await resp.json()
                        self._alarm.update(alarm_data)
                        return alarm_data.get('status')
            except Exception as e:
                _LOGGER.error(f"Failed to update alarm status: {e}")
        return None

    async def create_alarm(self, alarm_types=["police"]):
        """Create a new alarm using direct Noonlight API"""
        services = {}
        for alarm_type in alarm_types or ():
            if alarm_type in ["police", "fire", "medical"]:
                services[alarm_type] = True
        
        if self._alarm is None:
            try:
                # Build alarm payload
                alarm_body = {
                    "name": "Home Assistant Alarm",
                    "phone": self.config[CONF_PHONE_NUMBER],
                }
                
                # Add location
                if len(self.addline1) > 0:
                    alarm_body["location"] = {
                        "address": {
                            "line1": self.addline1,
                            "city": self.addcity,
                            "state": self.addstate,
                            "zip": self.addzip,
                            "country": self.addcountry,
                        }
                    }
                    if len(self.addline2) > 0:
                        alarm_body["location"]["address"]["line2"] = self.addline2
                else:
                    alarm_body["location"] = {
                        "coordinates": {
                            "lat": self.latitude,
                            "lng": self.longitude,
                            "accuracy": 5,
                        }
                    }
                
                # Add services if specified
                if len(services) > 0:
                    alarm_body["services"] = services
                
                # Make API call to create alarm
                url = f"{self.api_endpoint}/alarms"
                async with self._websession.post(url, json=alarm_body, headers=self.headers) as resp:
                    if resp.status == 201:
                        self._alarm = await resp.json()
                        _LOGGER.info(f"Alarm created successfully: {self._alarm.get('id')}")
                    else:
                        error_text = await resp.text()
                        raise Exception(f"API returned {resp.status}: {error_text}")
                        
            except Exception as client_error:
                persistent_notification.create(
                    self.hass,
                    "Failed to send an alarm to Noonlight!\n\n"
                    "({}: {})".format(type(client_error).__name__, str(client_error)),
                    "Noonlight Alarm Failure",
                    NOTIFICATION_ALARM_CREATE_FAILURE,
                )
                return
                
            if self._alarm and self._alarm.get('status') == CONST_ALARM_STATUS_ACTIVE:
                async_dispatcher_send(self.hass, EVENT_NOONLIGHT_ALARM_CREATED)
                _LOGGER.debug(
                    "noonlight alarm has been initiated. " "id: %s status: %s",
                    self._alarm.get('id'),
                    self._alarm.get('status'),
                )
                cancel_interval = None

                async def check_alarm_status_interval(now):
                    _LOGGER.debug("checking alarm status...")
                    if await self.update_alarm_status() == CONST_ALARM_STATUS_CANCELED:
                        _LOGGER.debug("alarm %s has been canceled!", self._alarm.get('id'))
                        if cancel_interval is not None:
                            cancel_interval()
                        if self._alarm is not None:
                            if self._alarm.get('status') == CONST_ALARM_STATUS_CANCELED:
                                self._alarm = None
                        async_dispatcher_send(self.hass, EVENT_NOONLIGHT_ALARM_CANCELED)

                cancel_interval = async_track_time_interval(
                    self.hass, check_alarm_status_interval, timedelta(seconds=15)
                )
