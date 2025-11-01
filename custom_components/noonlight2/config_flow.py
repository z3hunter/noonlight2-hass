import logging
from typing import TYPE_CHECKING, Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ID, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_ADDRESS_LINE1,
    CONF_ADDRESS_LINE2,
    CONF_API_ENDPOINT,
    CONF_CITY,
    CONF_LOCATION_MODE,
    CONF_PHONE_NUMBER,
    CONF_SERVER_TOKEN,
    CONF_STATE,
    CONF_ZIP,
    CONF_COUNTRY,
    CONF_USER_NAME,
    CONF_PIN,
    DEFAULT_API_ENDPOINT,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
LOCATION_MODE_LIST = [
    selector.SelectOptionDict(label="Use Latitude/Longitude", value="latlong"),
    selector.SelectOptionDict(label="Use Address", value="address"),
]

COUNTRY_LIST = [
    selector.SelectOptionDict(label="Canada", value="CA"),
    selector.SelectOptionDict(label="United States", value="US"),
]

PROVINCES = [
    "AB",
    "BC",
    "MB",
    "NB",
    "NL",
    "NS",
    "NT",
    "NU",
    "ON",
    "PE",
    "QC",
    "SK",
    "YT",
]

STATES = [
    "AK",
    "AL",
    "AR",
    "AZ",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "IA",
    "ID",
    "IL",
    "IN",
    "KS",
    "KY",
    "LA",
    "MA",
    "MD",
    "ME",
    "MI",
    "MN",
    "MO",
    "MS",
    "MT",
    "NC",
    "ND",
    "NE",
    "NH",
    "NJ",
    "NM",
    "NV",
    "NY",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VA",
    "VT",
    "WA",
    "WI",
    "WV",
    "WY",
]


async def _async_build_noonlight_schema(
    hass: HomeAssistant, user_input: list, default_dict: list
) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> Any:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema(
        {
            # Integration name
            vol.Required(
                CONF_NAME,
                default=_get_default(CONF_NAME),
            ): selector.TextSelector(selector.TextSelectorConfig()),

            # User's full name
            vol.Required(
                CONF_USER_NAME,
                description={"name": "Your Name"},
                default=_get_default(CONF_USER_NAME),
            ): selector.TextSelector(selector.TextSelectorConfig()),

            # Server token
            vol.Required(
                CONF_SERVER_TOKEN,
                default=_get_default(CONF_SERVER_TOKEN),
            ): selector.TextSelector(selector.TextSelectorConfig()),

            # Phone number
            vol.Required(
                CONF_PHONE_NUMBER,
                description={
                    "name": "Phone Number (14385550000)",
                    "suggested_value": _get_default(CONF_PHONE_NUMBER),
                },
            ): selector.TextSelector(selector.TextSelectorConfig()),

            # PIN
            vol.Required(
                CONF_PIN,
                description={"name": "Security PIN (4–6 digits)"},
                default=_get_default(CONF_PIN),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),

            # API endpoint
            vol.Required(
                CONF_API_ENDPOINT,
                default=_get_default(CONF_API_ENDPOINT),
            ): selector.TextSelector(selector.TextSelectorConfig()),

            # Country
            vol.Required(
                CONF_COUNTRY,
                default=_get_default(CONF_COUNTRY),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COUNTRY_LIST,
                    multiple=False,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),

            # Location mode
            vol.Required(
                CONF_LOCATION_MODE,
                default=_get_default(CONF_LOCATION_MODE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LOCATION_MODE_LIST,
                    multiple=False,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )
    return build_schema


async def _async_build_latlong_schema(
    hass: HomeAssistant, user_input: list, default_dict: list
) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema(
        {
            vol.Optional(
                CONF_LATITUDE,
                default=_get_default(CONF_LATITUDE),
            ): cv.latitude,
            vol.Optional(
                CONF_LONGITUDE,
                default=_get_default(CONF_LONGITUDE),
            ): cv.longitude,
        }
    )

    return build_schema


async def _async_build_address_schema_US(
    hass: HomeAssistant, user_input: list, default_dict: list
) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema({})

    if _get_default(CONF_ADDRESS_LINE1) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ADDRESS_LINE1,
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ADDRESS_LINE1,
                    default=_get_default(CONF_ADDRESS_LINE1),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    if _get_default(CONF_ADDRESS_LINE2) is None:
        build_schema = build_schema.extend(
            {
                vol.Optional(
                    CONF_ADDRESS_LINE2,
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Optional(
                    CONF_ADDRESS_LINE2,
                    default=_get_default(CONF_ADDRESS_LINE2),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    if _get_default(CONF_CITY) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_CITY,
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_CITY,
                    default=_get_default(CONF_CITY),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    if _get_default(CONF_STATE) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_STATE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=STATES,
                        multiple=False,
                        custom_value=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_STATE,
                    default=_get_default(CONF_STATE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=STATES,
                        multiple=False,
                        custom_value=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
    if _get_default(CONF_ZIP) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ZIP,
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ZIP,
                    default=_get_default(CONF_ZIP),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )

    return build_schema

async def _async_build_address_schema_CA(
    hass: HomeAssistant, user_input: list, default_dict: list
) -> Any:
    """Gets a schema for Canadian addresses using correct keys but localized labels."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> Any:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    build_schema = vol.Schema({})

    # Address line 1
    if _get_default(CONF_ADDRESS_LINE1) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(CONF_ADDRESS_LINE1): selector.TextSelector(
                    selector.TextSelectorConfig()
                ),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ADDRESS_LINE1,
                    default=_get_default(CONF_ADDRESS_LINE1),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )

    # Address line 2 (optional)
    if _get_default(CONF_ADDRESS_LINE2) is None:
        build_schema = build_schema.extend(
            {
                vol.Optional(CONF_ADDRESS_LINE2): selector.TextSelector(
                    selector.TextSelectorConfig()
                ),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Optional(
                    CONF_ADDRESS_LINE2,
                    default=_get_default(CONF_ADDRESS_LINE2),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )

    # City
    if _get_default(CONF_CITY) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(CONF_CITY): selector.TextSelector(
                    selector.TextSelectorConfig()
                ),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_CITY,
                    default=_get_default(CONF_CITY),
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )

    # Province (stored as CONF_STATE)
    if _get_default(CONF_STATE) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_STATE,
                    description={"name": "Province"},
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PROVINCES,
                        multiple=False,
                        custom_value=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_STATE,
                    default=_get_default(CONF_STATE),
                    description={"name": "Province"},
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PROVINCES,
                        multiple=False,
                        custom_value=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

    # Postal Code (stored as CONF_ZIP)
    if _get_default(CONF_ZIP) is None:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ZIP,
                    description={"name": "Postal Code"},
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )
    else:
        build_schema = build_schema.extend(
            {
                vol.Required(
                    CONF_ZIP,
                    default=_get_default(CONF_ZIP),
                    description={"name": "Postal Code"},
                ): selector.TextSelector(selector.TextSelectorConfig()),
            }
        )

    return build_schema

class Noonlight2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._errors = {}
        self._entry = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None, yaml_import: bool = False
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        self._errors = {}

        # User has submitted something
        if user_input is not None:
            self._data.update(user_input)

            if yaml_import:
                self._data.update(
                    {
                        CONF_NAME: DEFAULT_NAME,
                        CONF_LOCATION_MODE: "latlong",
                        CONF_LATITUDE: self.hass.config.latitude,
                        CONF_LONGITUDE: self.hass.config.longitude,
                    }
                )
                _LOGGER.debug(f"[async_step_user] self._data: {self._data}")
                return self.async_create_entry(
                    title=self._data[CONF_NAME], data=self._data
                )

            _LOGGER.debug(f"[async_step_user] self._data: {self._data}")

            # route based on country and mode
            if self._data.get(CONF_LOCATION_MODE) == "latlong":
                return await self.async_step_latlong()

            elif self._data.get(CONF_LOCATION_MODE) == "address":
                # make sure country was chosen
                if self._data.get(CONF_COUNTRY) == "US":
                    return await self.async_step_address()
                elif self._data.get(CONF_COUNTRY) == "CA":
                    return await self.async_step_address()
                else:
                    self._errors["base"] = "invalid_country"

        # first time or invalid input: show the initial form
        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_API_ENDPOINT: DEFAULT_API_ENDPOINT,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=await _async_build_noonlight_schema(
                self.hass, user_input, defaults
            ),
            errors=self._errors,
        )

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the address step."""

        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"[async_step_address] self._data: {self._data}")
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        # Defaults
        defaults = {}
        if self._data.get(CONF_COUNTRY) == "US":
            return self.async_show_form(
                step_id="address",
                data_schema=await _async_build_address_schema_US(
                    self.hass, user_input, defaults
                ),
                errors=self._errors,
            )
        elif self._data.get(CONF_COUNTRY) == "CA":
            return self.async_show_form(
                step_id="address",
                data_schema=await _async_build_address_schema_CA(
                    self.hass, user_input, defaults
                ),
                errors=self._errors,
            )

    async def async_step_latlong(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the latitude/longitude step."""

        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"[async_step_latlong] self._data: {self._data}")
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        # Defaults
        defaults = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
        }

        return self.async_show_form(
            step_id="latlong",
            data_schema=await _async_build_latlong_schema(
                self.hass, user_input, defaults
            ),
            errors=self._errors,
        )

    async def async_step_import(
        self, import_config: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Import a config entry from configuration.yaml."""

        if (
            import_config.get(CONF_SERVER_TOKEN, None) is None
            or import_config.get(CONF_API_ENDPOINT, None) is None
            or import_config.get(CONF_PHONE_NUMBER, None) is None
        ):
            _LOGGER.error(
                f"[Noonlight2] Invalid YAML Config. Cannot Import: {import_config}"
            )
            return
        _LOGGER.debug(f"[async_step_import] import_config: {import_config}")
        return await self.async_step_user(user_input=import_config, yaml_import=True)

    async def async_step_reconfigure(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if TYPE_CHECKING:
            assert entry is not None

        self._data = dict(entry.data)
        self._entry = entry
        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""

        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"[async_step_init] self._data: {self._data}")
            if self._data.get(CONF_LOCATION_MODE) == "latlong":
                return await self.async_step_reconfig_latlong()
            else:
                return await self.async_step_reconfig_address()

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=await _async_build_noonlight_schema(
                self.hass, user_input, self._data
            ),
            errors=self._errors,
        )

    async def async_step_reconfig_address(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the address step."""

        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            self._data.pop(CONF_LATITUDE, None)
            self._data.pop(CONF_LONGITUDE, None)
            if user_input.get(CONF_ADDRESS_LINE2, None) is None:
                self._data.pop(CONF_ADDRESS_LINE2, None)
            _LOGGER.debug(f"[async_step_reconfig_address] self._data: {self._data}")
            self.hass.config_entries.async_update_entry(self._entry, data=self._data)
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        if self._data.get(CONF_COUNTRY) == "US":
            return self.async_show_form(
                step_id="reconfig_address",
                data_schema=await _async_build_address_schema_US(
                    self.hass, user_input, self._data
                ),
                errors=self._errors,
            )
        elif self._data.get(CONF_COUNTRY) == "CA":
            return self.async_show_form(
                step_id="reconfig_address",
                data_schema=await _async_build_address_schema_CA(
                    self.hass, user_input, self._data
                ),
                errors=self._errors,
            )

    async def async_step_reconfig_latlong(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the latitude/longitude step."""

        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            self._data.pop(CONF_ADDRESS_LINE1, None)
            self._data.pop(CONF_ADDRESS_LINE2, None)
            self._data.pop(CONF_CITY, None)
            self._data.pop(CONF_STATE, None)
            self._data.pop(CONF_ZIP, None)
            self._data.pop(CONF_COUNTRY, None)
            _LOGGER.debug(f"[async_step_reconfig_latlong] self._data: {self._data}")
            self.hass.config_entries.async_update_entry(self._entry, data=self._data)
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfig_latlong",
            data_schema=await _async_build_latlong_schema(
                self.hass, user_input, self._data
            ),
            errors=self._errors,
        )
