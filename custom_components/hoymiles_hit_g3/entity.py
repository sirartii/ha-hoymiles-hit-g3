"""Common device identity, stable across gateway IP changes."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HITCoordinator


class HITEntity(CoordinatorEntity[HITCoordinator]):
    """Base for entities sharing one inverter and one poll."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HITCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hoymiles",
            model="HIT-G3",
            sw_version=str(coordinator.data["dsp_firmware"]),
        )

    @property
    def available(self) -> bool:
        """A missing optional measurement is unavailable, never a zero."""
        return super().available and self.coordinator.data.get(self._key) is not None
