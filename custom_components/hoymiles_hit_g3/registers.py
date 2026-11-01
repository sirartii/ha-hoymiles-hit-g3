"""A deliberately bounded FC04 map based on a working HIT-10L-G3 installation.

Addresses are zero based. Multiword values are high word first, big endian.
Divisors are protocol divisors, not Home Assistant YAML multipliers.
Legacy total-power placeholders (26, 45, 73, 77, 87, 91) are never exposed.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Register:
    """One physical input register value and its presentation metadata."""

    key: str
    name: str
    address: int
    dtype: str = "U16"
    divisor: int = 1
    unit: str | None = None
    device_class: str | None = None
    group: str = "core"
    diagnostic: bool = False
    enabled: bool = True
    minimum: float | None = None
    maximum: float | None = None

    @property
    def words(self) -> int:
        return 2 if self.dtype in ("I32", "U32", "H32") else 1


REGISTERS = (
    Register("operating_state", "Operating state", 0, maximum=6),
    Register("dsp_firmware", "Power DSP firmware", 1, diagnostic=True),
    Register("software_fault", "Software fault code", 19, "H32", diagnostic=True),
    Register("hardware_fault", "Hardware fault code", 21, "H32", diagnostic=True),
    *(
        register
        for string in range(1, 5)
        for register in (
            Register(
                f"pv{string}_voltage",
                f"PV{string} voltage",
                27 + (string - 1) * 3,
                divisor=10,
                unit="V",
                device_class="voltage",
                minimum=0,
                maximum=1200,
            ),
            Register(
                f"pv{string}_current",
                f"PV{string} current",
                28 + (string - 1) * 3,
                "I16",
                100,
                "A",
                "current",
                minimum=-1,
                maximum=100,
            ),
            Register(
                f"pv{string}_power",
                f"PV{string} power",
                29 + (string - 1) * 3,
                unit="W",
                device_class="power",
                minimum=0,
                maximum=40000,
            ),
        )
    ),
    Register(
        "battery_voltage",
        "Battery voltage",
        46,
        divisor=10,
        unit="V",
        device_class="voltage",
        group="battery",
        minimum=0,
        maximum=100,
    ),
    Register(
        "battery_current",
        "Battery current",
        48,
        "I32",
        100,
        "A",
        "current",
        group="battery",
        minimum=-1000,
        maximum=1000,
    ),
    Register(
        "battery_power",
        "Battery power",
        50,
        "I32",
        unit="W",
        device_class="power",
        group="battery",
        minimum=-60000,
        maximum=60000,
    ),
    Register(
        "dc_bus_voltage",
        "DC bus voltage",
        60,
        divisor=10,
        unit="V",
        device_class="voltage",
        diagnostic=True,
        minimum=0,
        maximum=1500,
    ),
    Register(
        "grid_frequency",
        "Grid frequency",
        66,
        divisor=100,
        unit="Hz",
        device_class="frequency",
        minimum=0,
        maximum=70,
    ),
    *(
        register
        for index, phase in enumerate(("a", "b", "c"))
        for register in (
            Register(
                f"inverter_voltage_{phase}",
                f"Inverter phase {phase.upper()} voltage",
                67 + index,
                divisor=10,
                unit="V",
                device_class="voltage",
                minimum=0,
                maximum=350,
            ),
            Register(
                f"inverter_current_{phase}",
                f"Inverter phase {phase.upper()} current",
                70 + index,
                "I16",
                100,
                "A",
                "current",
                minimum=-200,
                maximum=200,
            ),
            Register(
                f"inverter_power_{phase}",
                f"Inverter phase {phase.upper()} power",
                74 + index,
                "I16",
                unit="W",
                device_class="power",
            ),
            Register(
                f"eps_voltage_{phase}",
                f"EPS phase {phase.upper()} voltage",
                81 + index,
                divisor=10,
                unit="V",
                device_class="voltage",
                minimum=0,
                maximum=350,
            ),
            Register(
                f"eps_current_{phase}",
                f"EPS phase {phase.upper()} current",
                84 + index,
                "I16",
                100,
                "A",
                "current",
                minimum=-200,
                maximum=200,
            ),
            Register(
                f"eps_power_{phase}",
                f"EPS phase {phase.upper()} power",
                92 + index,
                "I16",
                unit="W",
                device_class="power",
            ),
        )
    ),
    Register(
        "inverter_temperature",
        "Inverter heatsink temperature",
        113,
        "I16",
        unit="°C",
        device_class="temperature",
        group="temperature",
        minimum=-40,
        maximum=150,
    ),
    Register(
        "battery_heatsink_temperature",
        "Battery heatsink temperature",
        114,
        "I16",
        unit="°C",
        device_class="temperature",
        group="temperature",
        minimum=-40,
        maximum=150,
    ),
    Register(
        "internal_temperature",
        "Internal temperature",
        115,
        "I16",
        unit="°C",
        device_class="temperature",
        group="temperature",
        minimum=-40,
        maximum=150,
    ),
    Register("bms_connected", "BMS connection", 1022, group="battery", maximum=1),
    Register(
        "battery_capacity",
        "Battery capacity",
        1024,
        divisor=10,
        unit="kWh",
        group="battery",
        minimum=0,
        maximum=500,
    ),
    Register(
        "battery_soc",
        "Battery state of charge",
        1025,
        unit="%",
        device_class="battery",
        group="battery",
        minimum=0,
        maximum=100,
    ),
    Register("grid_meter_connected", "Grid meter connection", 1046, group="meter", maximum=1),
    *(
        Register(
            f"grid_power_{phase}",
            f"Grid phase {phase.upper()} power",
            1078 + index * 2,
            "I32",
            unit="W",
            device_class="power",
            group="meter",
            minimum=-200000,
            maximum=200000,
        )
        for index, phase in enumerate(("a", "b", "c"))
    ),
    *(
        Register(key, name, address, "U32", 10, "kWh", "energy", group="energy")
        for key, name, address in (
            ("pv_energy", "PV energy", 2000),
            ("pv1_energy", "PV1 energy", 2002),
            ("pv2_energy", "PV2 energy", 2004),
            ("pv3_energy", "PV3 energy", 2006),
            ("pv4_energy", "PV4 energy", 2008),
            ("battery_charge_energy", "Battery charge energy", 2028),
            ("battery_discharge_energy", "Battery discharge energy", 2030),
            ("grid_import_energy", "Grid import energy", 2040),
            ("grid_export_energy", "Grid export energy", 2048),
            ("load_energy", "Load energy", 2056),
        )
    ),
    *(
        Register(key, name, address, divisor=10, unit="kWh", device_class="energy", group="daily")
        for key, name, address in (
            ("pv_energy_today", "PV energy today", 2100),
            ("battery_charge_energy_today", "Battery charge energy today", 2114),
            ("battery_discharge_energy_today", "Battery discharge energy today", 2115),
            ("grid_import_energy_today", "Grid import energy today", 2120),
            ("grid_export_energy_today", "Grid export energy today", 2124),
            ("load_energy_today", "Load energy today", 2128),
        )
    ),
    Register(
        "reported_load_power",
        "Reported load power",
        2169,
        "I16",
        unit="W",
        device_class="power",
        group="load",
        enabled=False,
        minimum=0,
    ),
)

# Fixed, small ranges known to respond on the reference installation. Do not scan
# the gap between the low telemetry addresses and the energy block.
READ_BLOCKS = (
    ("core", 0, 100),
    ("temperature", 113, 3),
    ("battery", 1021, 9),
    ("meter", 1046, 1),
    ("meter", 1078, 6),
    ("energy", 2000, 58),
    ("daily", 2100, 36),
    ("load", 2169, 1),
)


def decode_register(raw: dict[int, int], register: Register) -> int | float | str | None:
    """Decode signed values before applying scaling; reject incomplete/invalid data."""
    words = [raw.get(register.address + index) for index in range(register.words)]
    if any(word is None for word in words):
        return None
    value = 0
    for word in words:
        value = (value << 16) | word
    bits = register.words * 16
    if register.dtype.startswith("I") and value & (1 << (bits - 1)):
        value -= 1 << bits
    if register.dtype == "H32":
        return f"0x{value:08X}"
    scaled = value / register.divisor if register.divisor != 1 else value
    if register.minimum is not None and scaled < register.minimum:
        return None
    if register.maximum is not None and scaled > register.maximum:
        return None
    return scaled


def active_registers(
    pv_strings: int, has_battery: bool, has_grid_meter: bool
) -> tuple[Register, ...]:
    """Expose only hardware enabled in the configuration."""
    return tuple(
        reg
        for reg in REGISTERS
        if not (
            reg.key.startswith("pv") and reg.key[2:3].isdigit() and int(reg.key[2]) > pv_strings
        )
        and not (not has_battery and (reg.group == "battery" or reg.key.startswith("battery_")))
        and not (
            not has_grid_meter
            and (
                reg.group == "meter"
                or reg.key.startswith("grid_import_")
                or reg.key.startswith("grid_export_")
            )
        )
    )


def decode_snapshot(
    raw: dict[int, int],
    registers: tuple[Register, ...],
    pv_strings: int,
    positive_export: bool = True,
) -> dict:
    """Build a fresh snapshot; missing parts never turn into a fabricated zero."""
    values = {reg.key: decode_register(raw, reg) for reg in registers}
    if values.get("bms_connected") != 1:
        for key in tuple(values):
            if key in {
                "battery_voltage",
                "battery_current",
                "battery_power",
                "battery_capacity",
                "battery_soc",
            }:
                values[key] = None
    if values.get("grid_meter_connected") != 1:
        for phase in ("a", "b", "c"):
            if f"grid_power_{phase}" in values:
                values[f"grid_power_{phase}"] = None

    def total(key: str, parts: tuple[str, ...], multiplier: int = 1) -> None:
        components = [values.get(part) for part in parts]
        values[key] = (
            sum(components) * multiplier if all(value is not None for value in components) else None
        )

    total("pv_power", tuple(f"pv{string}_power" for string in range(1, pv_strings + 1)))
    total("inverter_power", tuple(f"inverter_power_{phase}" for phase in ("a", "b", "c")))
    total("eps_power", tuple(f"eps_power_{phase}" for phase in ("a", "b", "c")))
    if "grid_meter_connected" in values:
        total(
            "grid_net_power",
            tuple(f"grid_power_{phase}" for phase in ("a", "b", "c")),
            -1 if positive_export else 1,
        )
        power = values["grid_net_power"]
        values["grid_import_power"] = max(power, 0) if power is not None else None
        values["grid_export_power"] = max(-power, 0) if power is not None else None
    if "battery_power" in values:
        power = values["battery_power"]
        values["battery_charge_power"] = max(-power, 0) if power is not None else None
        values["battery_discharge_power"] = max(power, 0) if power is not None else None
    return values
