"""Telemetry and Energy dashboard sensors for HIT-G3."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_HAS_BATTERY, CONF_HAS_GRID_METER, OPERATING_STATES
from .coordinator import HITCoordinator
from .entity import HITEntity
from .registers import Register

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add physical sensors and power totals computed from valid components."""
    coordinator = entry.runtime_data
    entities = [
        HITSensor(coordinator, entry, register)
        for register in coordinator.registers
        if register.key not in ("bms_connected", "grid_meter_connected")
    ]
    totals = [
        ("pv_power", "PV power"),
        ("inverter_power", "Inverter power"),
        ("eps_power", "EPS power"),
    ]
    if coordinator.settings[CONF_HAS_BATTERY]:
        totals.extend(
            (
                ("battery_charge_power", "Battery charge power"),
                ("battery_discharge_power", "Battery discharge power"),
            )
        )
    if coordinator.settings[CONF_HAS_GRID_METER]:
        totals.extend(
            (
                ("grid_net_power", "Grid net power"),
                ("grid_import_power", "Grid import power"),
                ("grid_export_power", "Grid export power"),
            )
        )
    entities.extend(HITPowerSensor(coordinator, entry, key, name) for key, name in totals)
    async_add_entities(entities)


class HITSensor(HITEntity, SensorEntity):
    """A register with protocol units and Home Assistant statistics metadata."""

    def __init__(self, coordinator: HITCoordinator, entry: ConfigEntry, register: Register) -> None:
        super().__init__(coordinator, entry, register.key)
        self._register = register
        self._attr_name = register.name
        self._attr_native_unit_of_measurement = register.unit
        self._attr_entity_registry_enabled_default = register.enabled
        if register.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if register.device_class:
            self._attr_device_class = SensorDeviceClass(register.device_class)
            self._attr_state_class = (
                SensorStateClass.TOTAL_INCREASING
                if register.device_class == "energy"
                else SensorStateClass.MEASUREMENT
            )
        if register.key == "operating_state":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(OPERATING_STATES.values())
            self._attr_icon = "mdi:solar-power-variant"
        self._attr_suggested_display_precision = (
            (2 if register.unit in ("A", "Hz") else 1 if register.divisor != 1 else 0)
            if register.unit
            else None
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)
        return OPERATING_STATES.get(value) if self._key == "operating_state" else value

    @property
    def extra_state_attributes(self) -> dict:
        return {"input_register": self._register.address}


class HITPowerSensor(HITEntity, SensorEntity):
    """Computed totals with import/export split after summing all phases."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(
        self, coordinator: HITCoordinator, entry: ConfigEntry, key: str, name: str
    ) -> None:
        super().__init__(coordinator, entry, key)
        self._attr_name = name

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)
