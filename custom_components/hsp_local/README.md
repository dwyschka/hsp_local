# Haas+Sohn Stove (Local) – Home Assistant Custom Integration

Local (LAN) integration for Haas+Sohn pellet stoves. It talks **directly** to
the Wi-Fi module of the stove via the `status.cgi` HTTP interface and does not
use the Haas+Sohn cloud, so it keeps working without internet access.

It is modelled after Home Assistant's official
[`fumis`](https://www.home-assistant.io/integrations/fumis/) integration
(climate / sensor / switch / button entities) but uses the local protocol
instead of a cloud account.

## Requirements

- A Haas+Sohn pellet stove with the Wi-Fi module (`WLAN local`/`global`).
- The **IP address** of the module in your local network.
- The **PIN code** of the stove (Menu → Network → WLAN PIN, or on the label of
  the Wi-Fi module).

## Installation

1. Copy the `hsp_local` folder into your Home Assistant configuration
   directory:

   ```
   <config>/custom_components/hsp_local/
   ```

   The folder must contain `manifest.json` and all the Python files, and the
   `translations` subfolder.

2. Restart Home Assistant.

3. Go to **Settings → Devices & services → Add integration** and search for
   **Haas+Sohn Stove (Local)**.

4. Enter the IP address or hostname of the stove and the PIN code.

> The integration only needs the PIN to *send* commands. Reading the status is
> unauthenticated, so setup validates connectivity, not the PIN. If commands
> fail with an authentication error, double-check the PIN.

## Entities

| Platform        | Entity                     | Description                                   |
|-----------------|----------------------------|-----------------------------------------------|
| `climate`       | Stove                      | On/off, current and target temperature        |
| `sensor`        | Current temperature        | Room temperature (`is_temp`)                  |
| `sensor`        | Target temperature         | Target temperature (`sp_temp`)                |
| `sensor`        | Status                     | Raw stove mode (`mode`)                       |
| `sensor`        | Error                      | Active error code, `none` when there is none  |
| `sensor`        | Ignitions                  | Total ignitions (`ignitions`)                 |
| `sensor`        | Operating hours            | Total operating hours (`on_time`)             |
| `sensor`        | Consumption                | Total pellet consumption in kg (`consumption`)|
| `sensor`        | Maintenance in             | Pellets until next maintenance in kg           |
| `sensor`        | Cleaning in                | Hours until next cleaning (`cleaning_in`/60)  |
| `sensor`        | Heating curve              | Heating curve level (`ht_char`)               |
| `binary_sensor` | Week timer                 | Weekly program active (`wprg`)                |
| `binary_sensor` | PGI                        | `pgi` flag (disabled by default)              |
| `switch`        | Power                      | Turn the stove on/off (`prg`)                 |
| `switch`        | Weekly program             | Enable/disable the weekly program (`wprg`)    |
| `switch`        | Eco mode                   | Enable/disable eco mode (if supported)        |
| `button`        | Clear error                | Acknowledge the active error                  |

The **Weekly program** switch exposes the full weekly schedule as a
`schedule` attribute.

## Options

You can change the poll interval (in seconds, default `15`) via
**Configure** on the integration entry.

## Protocol notes

The Wi-Fi module exposes:

```
GET  http://<host>/status.cgi
POST http://<host>/status.cgi   (JSON body + X-HS-PIN header)
```

The `X-HS-PIN` header is `md5(nonce + md5_hex(pin))`, where `nonce` is read
from a fresh `GET` before every command. Commands used:

```json
{"prg": true}                 // power on/off
{"sp_temp": 22}               // target temperature
{"wprg": true}                // weekly program
{"eco_mode": true}            // eco mode
{"seen_error": [{"nr": 101}]} // acknowledge error
```

Thanks to the [`hsp-mqtt-bridge`](https://github.com/dwyschka/hsp-mqtt-bridge)
project and the openHAB Haas+Sohn binding for documenting the local protocol.

## License

This project is licensed under the [MIT License](../../LICENSE).
