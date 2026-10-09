# Haas+Sohn Stove (Local)

[![Validate](https://github.com/dwyschka/hsp_local/actions/workflows/validate.yml/badge.svg)](https://github.com/dwyschka/hsp_local/actions/workflows/validate.yml)

A Home Assistant **custom integration** for Haas+Sohn pellet stoves that talks
**directly** to the stove's Wi-Fi module over the local network. No cloud
account, no internet connection required.

It is inspired by the official Home Assistant
[`fumis`](https://www.home-assistant.io/integrations/fumis/) integration
(climate + sensors + switches + button), but speaks the local `status.cgi`
protocol instead of a cloud API.

## Features

- **Climate** entity: on/off, current and target room temperature.
- **Sensors**: current/target temperature, stove status (`mode`), error,
  ignitions, operating hours, pellet consumption, maintenance/cleaning
  countdown and heating curve.
- **Switches**: power, weekly program and eco mode.
- **Binary sensors**: week timer, PGI.
- **Button**: acknowledge the active error.
- Configurable poll interval.
- Local polling, no cloud, no external Python dependencies.

## Installation

### HACS (recommended)

1. Make sure [HACS](https://hacs.xyz) is installed.
2. Go to **HACS → Integrations**.
3. Open the three-dot menu (top right) and select **Custom repositories**.
4. Add the repository URL `https://github.com/dwyschka/hsp_local` with
   category **Integration**.
5. Search for **Haas+Sohn Stove (Local)** and install it.
6. Restart Home Assistant.

### Manual

Copy the folder `custom_components/hsp_local` into your Home Assistant
configuration directory (so you end up with
`<config>/custom_components/hsp_local/manifest.json`) and restart Home
Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Haas+Sohn Stove (Local)**.
3. Enter the IP address (or hostname) of the stove's Wi-Fi module and the PIN
   code. The PIN can be found on the stove under **Menu → Network → WLAN PIN**
   or on the label of the Wi-Fi module.

The PIN is only required to send commands; reading the status is
unauthenticated, so the setup validates connectivity, not the PIN. If commands
fail with an authentication error, double-check the PIN.

The poll interval (default 15 seconds) can be changed via **Configure** on the
integration entry.

## Entities

| Platform        | Entity                | Description                                      |
|-----------------|-----------------------|--------------------------------------------------|
| `climate`       | Stove                 | On/off, current and target temperature           |
| `sensor`        | Current temperature   | Room temperature (`is_temp`)                     |
| `sensor`        | Target temperature    | Target temperature (`sp_temp`)                   |
| `sensor`        | Status                | Raw stove mode (`mode`)                          |
| `sensor`        | Error                 | Active error code, `none` when there is none     |
| `sensor`        | Ignitions             | Total ignitions (`ignitions`)                    |
| `sensor`        | Operating hours       | Total operating hours (`on_time`)                |
| `sensor`        | Consumption           | Total pellet consumption in kg (`consumption`)   |
| `sensor`        | Maintenance in        | Pellets until next maintenance in kg              |
| `sensor`        | Cleaning in           | Hours until next cleaning (`cleaning_in`/60)     |
| `sensor`        | Heating curve         | Heating curve level (`ht_char`)                  |
| `binary_sensor` | Week timer            | Weekly program active (`wprg`)                   |
| `binary_sensor` | PGI                   | `pgi` flag (disabled by default)                 |
| `switch`        | Power                 | Turn the stove on/off (`prg`)                    |
| `switch`        | Weekly program        | Enable/disable the weekly program (`wprg`)       |
| `switch`        | Eco mode              | Enable/disable eco mode (if supported)           |
| `button`        | Clear error           | Acknowledge the active error                     |

The **Weekly program** switch exposes the full weekly schedule as a `schedule`
attribute.

## Protocol

The Wi-Fi module exposes a small JSON interface:

```
GET  http://<host>/status.cgi
POST http://<host>/status.cgi   (JSON body + X-HS-PIN header)
```

The `X-HS-PIN` header is `md5(nonce + md5_hex(pin))`, where `nonce` is read
from a fresh `GET` before every command. Supported commands:

```json
{"prg": true}                 // power on/off
{"sp_temp": 22}               // target temperature
{"wprg": true}                // weekly program
{"eco_mode": true}            // eco mode
{"seen_error": [{"nr": 101}]} // acknowledge error
```

## Credits

Protocol understanding based on the
[`hsp-mqtt-bridge`](https://github.com/dwyschka/hsp-mqtt-bridge) project and the
openHAB Haas+Sohn Pellet Stove binding.

## License

This project is licensed under the [MIT License](LICENSE).
