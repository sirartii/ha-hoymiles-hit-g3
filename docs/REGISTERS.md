# Register reference

All addresses are **zero-based input registers, function 04**. Multiword values use the high word first. The code divides by the listed divisor; a divisor of 10 is equivalent to a Home Assistant YAML scale of 0.1.

This is a bounded monitoring map derived from a working HIT-10L-G3 configuration, not a claim to implement every field in every firmware version.

| Measurement | Address | Type | Divisor |
| --- | --- | --- | --- |
| Operating state | 0 | U16 | 1 |
| Power DSP firmware | 1 | U16 | 1 |
| DRM mode code | 3 | U16 | 1 |
| Software / hardware fault masks | 19–20 / 21–22 | Hex U32 | 1 |
| PV1 voltage / current / power | 27 / 28 / 29 | U16 / I16 / U16 | 10 / 100 / 1 |
| PV2 voltage / current / power | 30 / 31 / 32 | U16 / I16 / U16 | 10 / 100 / 1 |
| PV3 voltage / current / power | 33 / 34 / 35 | U16 / I16 / U16 | 10 / 100 / 1 |
| PV4 voltage / current / power | 36 / 37 / 38 | U16 / I16 / U16 | 10 / 100 / 1 |
| Battery voltage | 46 | U16 | 10 |
| Battery current, G3 | 48–49 | I32 | 100 |
| Battery power, G3 | 50–51 | I32 | 1 |
| DC bus voltage | 60 | U16 | 10 |
| Grid frequency | 66 | U16 | 100 |
| Inverter phase voltage A/B/C | 67 / 68 / 69 | U16 | 10 |
| Inverter phase current A/B/C | 70 / 71 / 72 | I16 | 100 |
| Inverter phase active power A/B/C | 74 / 75 / 76 | I16 | 1 |
| Inverter phase reactive power A/B/C (var) | 78 / 79 / 80 | I16 | 1 |
| EPS phase voltage A/B/C | 81 / 82 / 83 | U16 | 10 |
| EPS phase current A/B/C | 84 / 85 / 86 | I16 | 100 |
| EPS phase active power A/B/C | 92 / 93 / 94 | I16 | 1 |
| Inverter / battery heatsink / internal temperature | 113 / 114 / 115 | I16 | 1 |
| Reported PV power, diagnostic | 190–191 | U32 | 1 |
| Battery maximum charge current (A) | 325 | U16 | 1 |
| Battery charge / discharge cutoff voltage (V) | 326 / 327 | U16 | 10 |
| Battery maximum discharge current (A) | 328 | U16 | 10 |
| BMS connection | 1022 | U16 | 1 |
| Battery capacity / SOC | 1024 / 1025 | U16 | 10 / 1 |
| Grid meter connection | 1046 | U16 | 1 |
| Grid phase active power A/B/C | 1078–1079 / 1080–1081 / 1082–1083 | I32 | 1 |
| PV lifetime energy | 2000–2001 | U32 | 10 |
| PV1 / PV2 / PV3 / PV4 lifetime energy | 2002 / 2004 / 2006 / 2008 (two words each) | U32 | 10 |
| Battery charge / discharge lifetime energy | 2028 / 2030 (two words each) | U32 | 10 |
| Grid import / export lifetime energy | 2040 / 2048 (two words each) | U32 | 10 |
| Load lifetime energy | 2056–2057 | U32 | 10 |
| PV energy today | 2100 | U16 | 10 |
| Battery charge / discharge energy today | 2114 / 2115 | U16 | 10 |
| Grid import / export energy today | 2120 / 2124 | U16 | 10 |
| Load energy today | 2128 | U16 | 10 |
| Reported load power, disabled by default | 2169 | I16 | 1 |

## Calculated values

- **PV power:** sum of all PV inputs selected in configuration. Any missing input makes the total unavailable.
- **Inverter power:** sum of phase active powers `74 + 75 + 76`.
- **Inverter reactive power:** signed sum of phase reactive powers `78 + 79 + 80`, in var.
- **EPS power:** sum of phase active powers `92 + 93 + 94`.
- **Battery charge/discharge power:** split the signed battery power into separate non-negative values. Positive raw power means discharge.
- **Grid net power:** sum all three meter phases, then normalize polarity so positive means import.
- **Grid import/export power:** split the normalized net power **after** summing phases. Simultaneous phase import and export are balanced.

This avoids legacy total-power placeholders at `26`, `45`, `73`, `77`, `87` and `91`. A legitimate measurement of 5 elsewhere is not discarded.

## Availability and limitations

The core telemetry block is required. Illegal-address responses from optional blocks leave their measurements unavailable. Each poll starts with a fresh register image, so a failed block never reuses a previous value. A disconnected BMS or grid meter invalidates its live measurements. Inverter lifetime energy counters remain independent of peripheral live status.

Battery limits come from an optional block read only when battery support is enabled. The limits describe inverter settings. DRM mode is reported as the raw code.

Fault masks are shown as hexadecimal codes. This release does not invent descriptions for undocumented fault bits. The rated-power field at `4` is used only as a basic plausibility check during setup, not as serial-number or exact-model detection.

The newer `1800` meter and `1900` BMS blocks are not required by this release. The optional reported PV power at `190–191` is available for comparison with the calculated PV power.
