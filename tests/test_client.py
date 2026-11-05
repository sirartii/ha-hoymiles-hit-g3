"""Exercise real pymodbus framing against a local, read-only TCP simulator."""

import asyncio
import struct
from contextlib import asynccontextmanager

import pytest

from custom_components.hoymiles_hit_g3.client import CannotConnect, HITClient, InvalidInverter

# Enable sockets after Home Assistant's setup hook blocks them for each test.
pytestmark = pytest.mark.usefixtures("socket_enabled")


@asynccontextmanager
async def modbus_server(raw, *, rejected=(), fail_core=False, truncate=False, disconnect=False):
    requests = []
    connections = set()

    async def handle(reader, writer):
        connections.add(writer)
        try:
            while True:
                header = await reader.readexactly(7)
                tid, protocol, length, unit = struct.unpack(">HHHB", header)
                pdu = await reader.readexactly(length - 1)
                function, start, count = struct.unpack(">BHH", pdu)
                requests.append((function, start, count, unit))
                assert protocol == 0 and function == 4 and unit == 1
                if disconnect:
                    return
                if start in rejected or (fail_core and start == 0):
                    response = bytes((0x84, 2))
                else:
                    words = [raw.get(start + offset, 0) for offset in range(count)]
                    if truncate:
                        words = words[:-1]
                    response = bytes((4, len(words) * 2)) + struct.pack(f">{len(words)}H", *words)
                packet = struct.pack(">HHHB", tid, 0, len(response) + 1, unit) + response
                # Real TCP responses may arrive in several fragments.
                writer.write(packet[:5])
                await writer.drain()
                await asyncio.sleep(0)
                writer.write(packet[5:])
                await writer.drain()
        except asyncio.IncompleteReadError, ConnectionError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            connections.discard(writer)

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = HITClient("127.0.0.1", port, 1, 0.2, request_delay=0)
    try:
        yield client, requests
    finally:
        client.close()
        server.close()
        await server.wait_closed()
        for writer in tuple(connections):
            writer.close()
            await writer.wait_closed()
        await asyncio.sleep(0)


async def test_real_modbus_framing_and_serialization(raw):
    async with modbus_server(raw) as (client, requests):
        first, second = await asyncio.gather(client.async_read(), client.async_read())
        assert first.registers[1025] == second.registers[1025] == 50
        assert first.unsupported_blocks == ()
        assert len(requests) == 20
        assert requests.count((4, 190, 2, 1)) == 2
        assert requests.count((4, 325, 4, 1)) == 2
        assert all(function == 4 for function, *_ in requests)


async def test_optional_illegal_address_is_isolated(raw):
    async with modbus_server(raw, rejected=(325, 2000)) as (client, _):
        result = await client.async_read()
        assert result.registers[0] == 3
        assert result.unsupported_blocks == (325, 2000)
        assert 325 not in result.registers
        assert 2000 not in result.registers
        assert result.registers[2100] == 200


async def test_disabling_hardware_skips_its_blocks(raw):
    async with modbus_server(raw) as (client, requests):
        await client.async_read(has_battery=False, has_grid_meter=False)
        assert not {325, 1021, 1046, 1078}.intersection(start for _, start, _, _ in requests)


@pytest.mark.parametrize("kwargs", [{"fail_core": True}, {"truncate": True}, {"disconnect": True}])
async def test_unusable_responses_fail_the_snapshot(raw, kwargs):
    async with modbus_server(raw, **kwargs) as (client, _):
        with pytest.raises(CannotConnect):
            await client.async_read()


async def test_wrong_device_is_rejected(raw):
    raw[4] = 0
    async with modbus_server(raw) as (client, _):
        with pytest.raises(InvalidInverter):
            await client.async_read()
