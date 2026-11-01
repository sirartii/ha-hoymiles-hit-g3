"""Download support data without host names, addresses or device names."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    coordinator = entry.runtime_data
    return {
        "settings": async_redact_data(coordinator.settings, {CONF_HOST, CONF_NAME}),
        "last_update_success": coordinator.last_update_success,
        "unsupported_input_blocks": coordinator.unsupported_blocks,
        "values": coordinator.data,
    }
