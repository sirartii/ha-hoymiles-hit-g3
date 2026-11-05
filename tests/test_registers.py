"""Check the actual G3 differences, signs, totals and failed-read behavior."""

import pytest

from custom_components.hoymiles_hit_g3.registers import (
    READ_BLOCKS,
    REGISTERS,
    Register,
    active_registers,
    decode_register,
    decode_snapshot,
)


def test_g3_current_power_frequency_and_unsigned_energy(raw):
    values = decode_snapshot(raw, active_registers(4, True, True), 4)
    assert values["battery_current"] == -20
    assert values["battery_power"] == -1040
    assert values["battery_charge_power"] == 1040
    assert values["battery_discharge_power"] == 0
    assert values["grid_frequency"] == 50
    assert values["pv_energy"] == 6000
    assert values["pv_power"] == 1600
    assert values["reported_pv_power"] == 1590
    assert values["inverter_power"] == 1800
    assert values["eps_power"] == 600
    assert (
        decode_register(
            {2000: 32768, 2001: 0}, next(reg for reg in REGISTERS if reg.key == "pv_energy")
        )
        == 214748364.8
    )


def test_net_grid_power_is_split_after_balancing_phases(raw):
    values = decode_snapshot(raw, active_registers(4, True, True), 4)
    assert values["grid_net_power"] == 300
    assert values["grid_import_power"] == 300
    assert values["grid_export_power"] == 0
    reverse = decode_snapshot(raw, active_registers(4, True, True), 4, positive_export=False)
    assert reverse["grid_import_power"] == 0
    assert reverse["grid_export_power"] == 300


def test_reactive_power_and_battery_limits_match_the_reference_scaling(raw):
    values = decode_snapshot(raw, active_registers(4, True, True), 4)
    assert values["drm_mode"] == 2
    assert values["inverter_reactive_power_a"] == -150
    assert values["inverter_reactive_power"] == -115
    assert values["battery_max_charge_current"] == 100
    assert values["battery_charge_cutoff_voltage"] == 56.5
    assert values["battery_discharge_cutoff_voltage"] == 44
    assert values["battery_max_discharge_current"] == 125


def test_missing_phase_does_not_make_a_false_zero(raw):
    raw.pop(1079)
    raw.pop(32)
    raw.pop(80)
    values = decode_snapshot(raw, active_registers(4, True, True), 4)
    assert values["grid_net_power"] is None
    assert values["grid_import_power"] is None
    assert values["grid_export_power"] is None
    assert values["pv_power"] is None
    assert values["inverter_power"] == 1800
    assert values["inverter_reactive_power"] is None


def test_offline_peripherals_do_not_erase_lifetime_counters(raw):
    raw[1022] = 0
    raw[1046] = 0
    values = decode_snapshot(raw, active_registers(4, True, True), 4)
    assert values["battery_power"] is None
    assert values["battery_soc"] is None
    assert values["grid_power_a"] is None
    assert values["grid_net_power"] is None
    assert values["battery_charge_energy"] == 1000
    assert values["grid_import_energy"] == 2000


def test_batteryless_two_input_system(raw):
    registers = active_registers(2, False, False)
    values = decode_snapshot(raw, registers, 2)
    assert values["pv_power"] == 800
    assert values["grid_frequency"] == 50
    assert "pv3_power" not in values
    assert "battery_power" not in values
    assert "battery_max_charge_current" not in values
    assert "bms_connected" not in values
    assert "grid_net_power" not in values


@pytest.mark.parametrize("soc", [101, 2005, 65535])
def test_invalid_soc_is_unavailable(raw, soc):
    raw[1025] = soc
    assert decode_snapshot(raw, active_registers(4, True, True), 4)["battery_soc"] is None


def test_fault_bits_and_negative_temperature():
    assert decode_register({19: 1, 20: 2}, Register("fault", "Fault", 19, "H32")) == "0x00010002"
    assert decode_register({115: 65526}, Register("temp", "Temperature", 115, "I16")) == -10


def test_read_ranges_cover_catalog_without_scanning_dead_zone():
    assert all(count <= 100 for _, _, count in READ_BLOCKS)
    assert not any(start < 1800 and start + count > 1101 for _, start, count in READ_BLOCKS)
    for reg in REGISTERS:
        assert any(
            start <= reg.address and start + count >= reg.address + reg.words
            for _, start, count in READ_BLOCKS
        )
    assert not {26, 45, 73, 77, 87, 91}.intersection(reg.address for reg in REGISTERS)
