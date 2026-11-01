"""Serialized, asynchronous, read-only Modbus TCP transport."""

import asyncio
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import REQUEST_DELAY
from .registers import READ_BLOCKS


class CannotConnect(Exception):
    """The gateway or inverter did not return a usable response."""


class InvalidInverter(Exception):
    """The mandatory status block is incompatible with this map."""


@dataclass(frozen=True)
class Snapshot:
    """Raw values and optional blocks rejected during this poll."""

    registers: dict[int, int]
    unsupported_blocks: tuple[int, ...]


class HITClient:
    """Only FC04 is exposed; no inverter write methods are provided."""

    def __init__(
        self,
        host: str,
        port: int,
        unit_id: int,
        timeout: int,
        *,
        request_delay: float = REQUEST_DELAY,
    ) -> None:
        self._client = AsyncModbusTcpClient(host, port=port, timeout=timeout, retries=0)
        self._unit_id = unit_id
        self._lock = asyncio.Lock()
        self._request_delay = request_delay

    def close(self) -> None:
        """Release the TCP connection, including automatic reconnect tasks."""
        self._client.close()

    async def async_read(
        self, *, has_battery: bool = True, has_grid_meter: bool = True
    ) -> Snapshot:
        """Read known blocks, preserving partial support without retaining stale data."""
        async with self._lock:
            try:
                if not self._client.connected and not await self._client.connect():
                    raise CannotConnect("Unable to connect to the Modbus TCP gateway")
                raw: dict[int, int] = {}
                unsupported: list[int] = []
                for group, address, count in READ_BLOCKS:
                    if group == "battery" and not has_battery:
                        continue
                    if group == "meter" and not has_grid_meter:
                        continue
                    if raw and self._request_delay:
                        await asyncio.sleep(self._request_delay)
                    response = await self._client.read_input_registers(
                        address, count=count, device_id=self._unit_id
                    )
                    if response.isError():
                        # Illegal function/address/value means this firmware does
                        # not implement the optional block. Gateway failures and
                        # transport errors must fail the snapshot instead.
                        code = getattr(response, "exception_code", None)
                        if group != "core" and code in (1, 2, 3):
                            unsupported.append(address)
                            continue
                        raise CannotConnect(f"Modbus error at input register {address}: {response}")
                    if len(response.registers) != count:
                        raise CannotConnect(f"Incomplete response at input register {address}")
                    raw.update(enumerate(response.registers, start=address))
                if raw.get(0) not in range(7) or not 1000 <= raw.get(4, 0) <= 25000:
                    raise InvalidInverter("Unexpected status or rated power in the HIT-G3 block")
                return Snapshot(raw, tuple(unsupported))
            except (OSError, TimeoutError, ModbusException) as err:
                self.close()
                raise CannotConnect("The gateway or inverter did not respond") from err
            except CannotConnect, InvalidInverter, asyncio.CancelledError:
                self.close()
                raise
