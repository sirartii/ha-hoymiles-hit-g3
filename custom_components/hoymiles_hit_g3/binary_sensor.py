"""Connection status reported by the inverter, independent of TCP reachability."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_HAS_BATTERY, CONF_HAS_GRID_METER
from .coordinator import HITCoordinator
from .entity import HITEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities = []
    if coordinator.settings[CONF_HAS_BATTERY]:
        entities.append(HITConnectionSensor(coordinator, entry, "bms_connected", "BMS connection"))
    if coordinator.settings[CONF_HAS_GRID_METER]:
        entities.append(
            HITConnectionSensor(coordinator, entry, "grid_meter_connected", "Grid meter connection")
        )
    async_add_entities(entities)


class HITConnectionSensor(HITEntity, BinarySensorEntity):
    """Distinguish an offline peripheral from an unavailable inverter."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: HITCoordinator, entry: ConfigEntry, key: str, name: str
    ) -> None:
        super().__init__(coordinator, entry, key)
        self._attr_name = name

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get(self._key) == 1
