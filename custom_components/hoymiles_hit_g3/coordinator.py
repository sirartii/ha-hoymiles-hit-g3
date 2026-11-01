"""Poll one inverter once for all entities."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CannotConnect, HITClient, InvalidInverter
from .const import (
    CONF_GRID_DIRECTION,
    CONF_HAS_BATTERY,
    CONF_HAS_GRID_METER,
    CONF_PV_STRINGS,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    POSITIVE_EXPORT,
)
from .registers import active_registers, decode_snapshot

_LOGGER = logging.getLogger(__name__)


class HITCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate serialized snapshots and recover on the next polling interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.settings = {**entry.data, **entry.options}
        self.client = HITClient(
            self.settings[CONF_HOST],
            self.settings[CONF_PORT],
            self.settings[CONF_UNIT_ID],
            self.settings[CONF_TIMEOUT],
        )
        self.registers = active_registers(
            self.settings[CONF_PV_STRINGS],
            self.settings[CONF_HAS_BATTERY],
            self.settings[CONF_HAS_GRID_METER],
        )
        self.unsupported_blocks: tuple[int, ...] = ()
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=self.settings.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            always_update=False,
        )

    async def _async_update_data(self) -> dict:
        try:
            snapshot = await self.client.async_read(
                has_battery=self.settings[CONF_HAS_BATTERY],
                has_grid_meter=self.settings[CONF_HAS_GRID_METER],
            )
        except (CannotConnect, InvalidInverter) as err:
            raise UpdateFailed(str(err)) from err
        self.unsupported_blocks = snapshot.unsupported_blocks
        return decode_snapshot(
            snapshot.registers,
            self.registers,
            self.settings[CONF_PV_STRINGS],
            self.settings[CONF_GRID_DIRECTION] == POSITIVE_EXPORT,
        )
