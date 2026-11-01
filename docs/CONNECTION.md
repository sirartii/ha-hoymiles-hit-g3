# Connect a Modbus TCP–RS485 gateway to HIT-G3

## Hardware

Use an RS485 gateway that **translates Modbus TCP requests into Modbus RTU**. Power it according to its own manual. A bare RS485 transceiver, USB adapter or transparent serial TCP server is not a substitute for this gateway mode in version 0.1.0.

```text
Home Assistant    Ethernet / Wi-Fi     TCP-to-RTU gateway       HIT-L-G3
    FC04  ──────────────────────────►  Modbus TCP server
                                      RS485 A  ─────────────  485A
                                      RS485 B  ─────────────  485B
```

## Inverter connector

The HIT-L-G3 manual's COM1 **Parallel** connector identifies these RS485 pins. The external port is commonly labelled **Parallel_2 / PARA2**. An installer must confirm the port function and pin orientation against the **exact inverter revision** before making the cable.

| Inverter connector | Signal | Gateway terminal |
| --- | --- | --- |
| Pin 8 | 485A | RS485 A |
| Pin 7 | 485B | RS485 B |

Use a twisted pair. Wire a signal reference or shield only as directed by the gateway and inverter manuals; do not substitute protective earth for a signal terminal. Termination and biasing must follow the manuals for the actual bus layout. Do not add resistors blindly to an already terminated bus.

The communication connector is **not Ethernet**, even though it uses an RJ45-shaped socket. Do not connect it to a LAN switch or inject PoE. Do not connect the gateway to the inverter's Meter or BMS bus. Do not attach another Modbus master to an active parallel communications bus without an approved topology.

An authorized installer should perform wiring with the equipment isolated according to the manufacturer's procedure.

## Gateway settings

| Setting | Reference installation |
| --- | --- |
| Network mode | Modbus TCP server → Modbus RTU master |
| TCP port | 502 |
| RS485 speed | 115200 baud |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Inverter address / unit ID | 1 |
| Address offset | 0; addresses in the code are zero based |
| Word and byte order | High word first, big endian |

These values worked on the reference HIT-10L-G3. If the inverter address or baud rate has already been changed, match its actual configuration. Some gateways have separate settings for TCP unit-ID forwarding or mapping; the request must reach the inverter's configured RTU address.

Use a fixed address or DHCP reservation for the gateway. Home Assistant connects to the **gateway's LAN address**, not a cloud endpoint. Keep port 502 private to the LAN.

## Home Assistant

Install the repository through HACS, restart Home Assistant, and add **Hoymiles HIT-G3** in Devices & services. Enter the gateway address, port and unit ID. Start with a **15-second poll** and **3-second timeout**. Select the PV inputs, battery and external meter actually present.

Before setup, stop the old YAML Modbus hub and any other third-party polling tool using the same bus. The integration serializes all its own requests, but cannot coordinate with another master.

Verify PV power, battery SOC and grid direction against the inverter display or portal. BMS or meter readings are unavailable when the corresponding inverter link-status register reports no connection; a successful TCP connection alone does not confirm peripheral communication.

## Sources

- [Hoymiles manuals](https://www.hoymiles.com/download/): HIT-(5–20)L-G3, COM1 connection.
- [V2C's direct Hoymiles RS485 guide](https://v2charge.com/support/power-control/dynamic/photovoltaic/inverter-hoymiles/): PARA2 pins 7/8 and factory serial settings. Its Trydan-specific change to 9600 baud is not needed for a gateway operating at 115200 baud.
