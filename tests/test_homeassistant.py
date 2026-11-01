"""Test actual Home Assistant setup, forms, entities, options and cleanup."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hoymiles_hit_g3.client import CannotConnect, InvalidInverter, Snapshot
from custom_components.hoymiles_hit_g3.config_flow import endpoint_id
from custom_components.hoymiles_hit_g3.const import DOMAIN
from custom_components.hoymiles_hit_g3.diagnostics import async_get_config_entry_diagnostics

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture
def mock_client(raw):
    with patch("custom_components.hoymiles_hit_g3.coordinator.HITClient") as factory:
        factory.return_value.async_read = AsyncMock(return_value=Snapshot(raw, ()))
        yield factory.return_value


async def test_setup_statistics_metadata_outage_recovery_and_unload(
    hass, settings, mock_client, raw
):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Test HIT", data=settings, unique_id=endpoint_id(settings)
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    registry = er.async_get(hass)

    def entity(key):
        return registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}")

    power = hass.states.get(entity("pv_power"))
    assert power.state == "1600"
    energy = hass.states.get(entity("pv_energy"))
    assert energy.state == "6000.0"
    assert energy.attributes["device_class"] == "energy"
    assert energy.attributes["state_class"] == "total_increasing"
    assert energy.attributes["unit_of_measurement"] == "kWh"
    assert hass.states.get(entity("operating_state")).state == "grid_connected"
    assert hass.states.get(entity("grid_import_power")).state == "300"
    mock_client.async_read.side_effect = CannotConnect("Simulated outage")
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity("pv_power")).state == STATE_UNAVAILABLE
    mock_client.async_read.side_effect = None
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity("pv_power")).state == "1600"
    raw.pop(1079)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity("grid_import_power")).state == STATE_UNAVAILABLE
    assert hass.states.get(entity("pv_power")).state == "1600"
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert settings["host"] not in str(diagnostics)
    assert settings["name"] not in str(diagnostics)
    assert await hass.config_entries.async_unload(entry.entry_id)
    mock_client.close.assert_called_once()


async def test_failed_first_refresh_closes_connection(hass, settings, mock_client):
    mock_client.async_read.side_effect = CannotConnect("Offline")
    entry = MockConfigEntry(domain=DOMAIN, data=settings)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    mock_client.close.assert_called_once()


async def test_config_flow_validates_and_prevents_duplicates(hass, settings):
    with (
        patch(
            "custom_components.hoymiles_hit_g3.config_flow.async_validate", new_callable=AsyncMock
        ) as validate,
        patch("custom_components.hoymiles_hit_g3.async_setup_entry", return_value=True),
    ):
        form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert form["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(form["flow_id"], settings)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        validate.assert_awaited_once()
        await hass.async_block_till_done()
        form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        duplicate = await hass.config_entries.flow.async_configure(form["flow_id"], settings)
        assert duplicate["type"] is FlowResultType.ABORT
        assert duplicate["reason"] == "already_configured"


@pytest.mark.parametrize(
    "error, expected", [(CannotConnect, "cannot_connect"), (InvalidInverter, "invalid_inverter")]
)
async def test_config_flow_reports_connection_errors(hass, settings, error, expected):
    with patch("custom_components.hoymiles_hit_g3.config_flow.async_validate", side_effect=error):
        form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(form["flow_id"], settings)
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": expected}


async def test_reconfigure_keeps_identity_and_clears_old_options(hass, settings):
    entry = MockConfigEntry(
        domain=DOMAIN, data=settings, unique_id=endpoint_id(settings), options={"timeout": 9}
    )
    entry.add_to_hass(hass)
    updated = {**settings, "host": "192.0.2.11", "timeout": 4}
    with (
        patch(
            "custom_components.hoymiles_hit_g3.config_flow.async_validate", new_callable=AsyncMock
        ),
        patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock),
    ):
        form = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
        )
        result = await hass.config_entries.flow.async_configure(form["flow_id"], updated)
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.data["host"] == "192.0.2.11"
        assert entry.data["timeout"] == 4
        assert entry.options == {}
        assert entry.unique_id == endpoint_id(updated)
        await hass.async_block_till_done()


async def test_options_reload(hass, settings, mock_client):
    entry = MockConfigEntry(domain=DOMAIN, data=settings)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock) as reload:
        form = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            form["flow_id"], {"scan_interval": 30, "timeout": 5}
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
        reload.assert_awaited_once_with(entry.entry_id)
    await hass.config_entries.async_unload(entry.entry_id)
