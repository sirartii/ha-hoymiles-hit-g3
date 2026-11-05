# Changelog

## 0.1.3 — 2026-11-05

- Fix the gateway address field so Home Assistant can display the setup and reconfiguration forms.

## 0.1.2 — 2026-11-05

- Read DRM mode and the inverter's reactive power on each phase. Calculate total reactive power from all three phases.
- Read battery charge and discharge current limits and cutoff voltages from an optional register block.
- Expose the inverter's reported PV total for comparison with the sum of the PV inputs.
- Document installation from the default HACS catalogue.

## 0.1.1 — 2026-11-01

- Enable every HACS validation check, including local brand assets, for submission to the default catalogue.
- Inverter monitoring behavior and configuration are unchanged from 0.1.0.

## 0.1.0 — 2026-11-01

Initial public release for local, read-only monitoring of Hoymiles HIT-L-G3 inverters.

- Home Assistant setup, polling options and gateway reconfiguration through the UI.
- G3 signed 32-bit battery current and power.
- Calculated PV, inverter and EPS totals that avoid legacy placeholder registers.
- Three-phase grid power balancing before splitting import and export.
- Inverter energy counters with Energy dashboard metadata.
- Peripheral connection status, optional-block handling, outage recovery and diagnostics.
- English documentation, connection instructions and register reference.
- Automated protocol, decoding and Home Assistant tests, plus HACS and hassfest checks.

Hardware reference: HIT-10L-G3. Other power classes and firmware revisions need independent verification. HACS installation is through a custom repository; default-catalogue inclusion is not claimed.
