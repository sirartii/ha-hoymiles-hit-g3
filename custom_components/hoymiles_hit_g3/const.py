"""Configuration shared by the Hoymiles HIT-G3 integration."""

DOMAIN = "hoymiles_hit_g3"
DEFAULT_NAME = "Hoymiles HIT-G3"
CONF_UNIT_ID = "unit_id"
CONF_PV_STRINGS = "pv_strings"
CONF_HAS_BATTERY = "has_battery"
CONF_HAS_GRID_METER = "has_grid_meter"
CONF_GRID_DIRECTION = "grid_direction"
POSITIVE_EXPORT = "positive_export"
POSITIVE_IMPORT = "positive_import"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 15
DEFAULT_TIMEOUT = 3
DEFAULT_PV_STRINGS = 4
REQUEST_DELAY = 0.05

OPERATING_STATES = {
    0: "power_up",
    1: "standby",
    2: "grid_check",
    3: "grid_connected",
    4: "fault",
    5: "islanded",
    6: "bypass",
}
