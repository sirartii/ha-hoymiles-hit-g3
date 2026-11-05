"""Set up and reconfigure a Modbus TCP gateway through the Home Assistant UI."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import callback

from .client import CannotConnect, HITClient, InvalidInverter
from .const import (
    CONF_GRID_DIRECTION,
    CONF_HAS_BATTERY,
    CONF_HAS_GRID_METER,
    CONF_PV_STRINGS,
    CONF_UNIT_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_PV_STRINGS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    POSITIVE_EXPORT,
    POSITIVE_IMPORT,
)


def connection_schema(defaults: dict[str, Any]) -> vol.Schema:
    """The host has no private-network default or embedded installation data."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(
                CONF_UNIT_ID, default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
            vol.Required(
                CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            vol.Required(
                CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=15)),
            vol.Required(
                CONF_PV_STRINGS, default=defaults.get(CONF_PV_STRINGS, DEFAULT_PV_STRINGS)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
            vol.Required(CONF_HAS_BATTERY, default=defaults.get(CONF_HAS_BATTERY, True)): bool,
            vol.Required(
                CONF_HAS_GRID_METER, default=defaults.get(CONF_HAS_GRID_METER, True)
            ): bool,
            vol.Required(
                CONF_GRID_DIRECTION, default=defaults.get(CONF_GRID_DIRECTION, POSITIVE_EXPORT)
            ): vol.In((POSITIVE_EXPORT, POSITIVE_IMPORT)),
        }
    )


def normalized_settings(settings: dict) -> dict:
    """Avoid duplicate entries caused by whitespace or host letter case."""
    return {
        **settings,
        CONF_HOST: settings[CONF_HOST].strip().lower(),
        CONF_NAME: settings[CONF_NAME].strip() or DEFAULT_NAME,
    }


def endpoint_id(settings: dict) -> str:
    return f"{settings[CONF_HOST]}:{settings[CONF_PORT]}:{settings[CONF_UNIT_ID]}"


async def async_validate(settings: dict) -> None:
    """Test real inverter responses, not just an open TCP port."""
    if not settings[CONF_HOST]:
        raise CannotConnect("The gateway address is empty")
    client = HITClient(
        settings[CONF_HOST], settings[CONF_PORT], settings[CONF_UNIT_ID], settings[CONF_TIMEOUT]
    )
    try:
        await client.async_read(
            has_battery=settings[CONF_HAS_BATTERY], has_grid_meter=settings[CONF_HAS_GRID_METER]
        )
    finally:
        client.close()


class HITConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One config entry per gateway port and inverter unit ID."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            user_input = normalized_settings(user_input)
            await self.async_set_unique_id(endpoint_id(user_input))
            self._abort_if_unique_id_configured()
            try:
                await async_validate(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidInverter:
                errors["base"] = "invalid_inverter"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=connection_schema(user_input or {}), errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict | None = None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            user_input = normalized_settings(user_input)
            for other in self._async_current_entries():
                if other.entry_id != entry.entry_id and other.unique_id == endpoint_id(user_input):
                    return self.async_abort(reason="already_configured")
            try:
                await async_validate(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidInverter:
                errors["base"] = "invalid_inverter"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    title=user_input[CONF_NAME],
                    unique_id=endpoint_id(user_input),
                    data=user_input,
                    options={},
                )
        return self.async_show_form(
            step_id="reconfigure",
            errors=errors,
            data_schema=connection_schema(user_input or {**entry.data, **entry.options}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HITOptionsFlow()


class HITOptionsFlow(config_entries.OptionsFlowWithReload):
    """Tune polling without adding a duplicate device."""

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        settings = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=settings[CONF_SCAN_INTERVAL]): vol.All(
                        vol.Coerce(int), vol.Range(min=5, max=300)
                    ),
                    vol.Required(CONF_TIMEOUT, default=settings[CONF_TIMEOUT]): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=15)
                    ),
                }
            ),
        )
