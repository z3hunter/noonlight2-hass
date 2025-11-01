"""Create a switch to trigger an alarm in Noonlight."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    EVENT_NOONLIGHT_ALARM_CANCELED,
    EVENT_NOONLIGHT_ALARM_CREATED,
    EVENT_NOONLIGHT_TOKEN_REFRESHED,
)

DEFAULT_NAME = "Noonlight2 Switch"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Setup the sensor platform with a config_entry (config_flow)."""

    _LOGGER.debug(f"[aync_setup_entry] noonlight_integration: {hass.data.get(DOMAIN)}")
    _LOGGER.debug(f"[aync_setup_entry] config_entry: {config_entry.data}")

    noonlight_integration = hass.data.get(DOMAIN).get(config_entry.entry_id)
    noonlight_switch = NoonlightSwitch(noonlight_integration)
    async_add_entities([noonlight_switch])

    def noonlight_token_refreshed():
        noonlight_switch.schedule_update_ha_state()

    def noonlight_alarm_canceled():
        noonlight_switch._state = False
        noonlight_switch.schedule_update_ha_state()

    def noonlight_alarm_created():
        noonlight_switch._state = True
        noonlight_switch.schedule_update_ha_state()

    async_dispatcher_connect(
        hass, EVENT_NOONLIGHT_TOKEN_REFRESHED, noonlight_token_refreshed
    )

    async_dispatcher_connect(
        hass, EVENT_NOONLIGHT_ALARM_CANCELED, noonlight_alarm_canceled
    )

    async_dispatcher_connect(
        hass, EVENT_NOONLIGHT_ALARM_CREATED, noonlight_alarm_created
    )


class NoonlightSwitch(SwitchEntity):
    """Noonlight Alarm Switch."""

    def __init__(self, noonlight_integration):
        """Initialize the Noonlight switch."""
        self.noonlight = noonlight_integration
        self._alarm_type = "police"
        self._attr_unique_id = f"{self._alarm_type.lower()}_{Platform.SWITCH}_{
            self.noonlight.config.get('id', '')}"
        self._attr_name = DEFAULT_NAME
        self._attr_icon = "mdi:police-badge"
        self._state = False

    @property
    def available(self):
        """Ensure that the Noonlight server token is valid."""
        return bool(self.noonlight.server_token)

    @property
    def extra_state_attributes(self):
        """Return the current alarm attributes, when active."""
        attr = {}
        if self.noonlight._alarm is not None:
            alarm = self.noonlight._alarm
            attr["alarm_status"] = alarm.get('status')
            attr["alarm_id"] = alarm.get('id')
            attr["alarm_services"] = alarm.get('services', {})
        return attr

    @property
    def is_on(self):
        """Return the status of the switch."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Activate an alarm. Defaults to `police` services."""
        if self.noonlight._alarm is None:
            await self.noonlight.create_alarm()
            if self.noonlight._alarm is not None:
                self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off the switch if the active alarm is canceled."""
        if self.noonlight._alarm is None:
            self._state = False
