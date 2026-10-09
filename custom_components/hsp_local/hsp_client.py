"""Local HTTP client for Haas+Sohn pellet stoves (``status.cgi``).

The Wi-Fi module of Haas+Sohn pellet stoves exposes a small JSON interface:

* ``GET  http://<host>/status.cgi`` returns the complete stove status,
  including a one-time ``nonce`` inside ``meta``.
* ``POST http://<host>/status.cgi`` with a JSON body sends a command. The
  request must carry the ``X-HS-PIN`` header, which is
  ``md5(nonce + md5_hex(pin))``.

The nonce changes with every request, so a fresh ``GET`` is performed before
each command to compute a valid header.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from .const import BACKEND_IP

REQUEST_TIMEOUT = 10


class HspError(Exception):
    """Base class for Haas+Sohn errors."""


class HspConnectionError(HspError):
    """Raised when the stove cannot be reached."""


class HspAuthError(HspError):
    """Raised when the stove rejects the PIN."""


class HspParseError(HspError):
    """Raised when the stove response cannot be parsed."""


@dataclass(slots=True)
class HspMeta:
    """Metadata reported by the stove."""

    sw_version: str = ""
    hw_version: str = ""
    bootl_version: str = ""
    wifi_sw_version: str = ""
    wifi_bootl_version: str = ""
    sn: str = ""
    typ: str = ""
    language: str = ""
    nonce: str = ""
    ean: str = ""
    eco_editable: bool = False
    ts: int = 0
    rau: bool = False
    wlan_features: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HspWeekProgramEntry:
    """A single weekly-program schedule entry."""

    day: str = ""
    begin: str = ""
    end: str = ""
    temperature: int | None = None


@dataclass(slots=True)
class HspStoveError:
    """An active stove error."""

    time: str = ""
    nr: int | None = None


@dataclass(slots=True)
class HspStatus:
    """Parsed stove status."""

    meta: HspMeta
    power: bool
    week_program: bool
    mode: str
    target_temperature: float | None
    current_temperature: float | None
    heating_curve: int | None
    week_program_schedule: list[HspWeekProgramEntry]
    errors: list[HspStoveError]
    eco_mode: bool
    pgi: bool
    ignitions: int | None
    on_time: int | None
    consumption: int | None
    maintenance_in: int | None
    cleaning_in: int | None


class HspClient:
    """Thin async client around the stove's ``status.cgi`` endpoint."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, pin: str
    ) -> None:
        """Initialize the client."""
        self._session = session
        host = host.strip()
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"
        self._base_url = host.rstrip("/")
        self._pin = pin
        self._timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    @property
    def base_url(self) -> str:
        """Return the base URL of the stove."""
        return self._base_url

    @property
    def status_url(self) -> str:
        """Return the status URL."""
        return f"{self._base_url}/status.cgi"

    async def async_get_status(self) -> HspStatus:
        """Fetch and parse the current stove status."""
        return _parse_status(await self._async_get_raw())

    async def async_send_command(self, payload: dict[str, Any]) -> HspStatus:
        """Send a command to the stove and return the resulting status."""
        # The nonce is only valid for a single request, so fetch a fresh one.
        raw = await self._async_get_raw()
        nonce = _parse_meta(raw).nonce

        headers = {
            "X-HS-PIN": _calculate_pin(nonce, self._pin),
            "X-BACKEND-IP": BACKEND_IP,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "ios",
        }

        try:
            async with self._session.post(
                self.status_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=self._timeout,
            ) as response:
                if response.status in (401, 403):
                    raise HspAuthError(
                        f"Authentication failed (HTTP {response.status})"
                    )
                if response.status >= 400:
                    raise HspConnectionError(
                        f"Unexpected HTTP {response.status} from stove"
                    )
                body = await response.text()
        except HspError:
            raise
        except TimeoutError as err:
            raise HspConnectionError("Timeout while sending command") from err
        except aiohttp.ClientError as err:
            raise HspConnectionError(str(err)) from err

        try:
            return _parse_status(json.loads(body))
        except ValueError:
            # Some firmware revisions answer a POST with an empty body.
            return await self.async_get_status()

    async def async_set_power(self, turn_on: bool) -> HspStatus:
        """Turn the stove on or off."""
        return await self.async_send_command({"prg": turn_on})

    async def async_set_target_temperature(self, temperature: float) -> HspStatus:
        """Set the target room temperature."""
        return await self.async_send_command({"sp_temp": temperature})

    async def async_set_eco_mode(self, enabled: bool) -> HspStatus:
        """Enable or disable eco mode."""
        return await self.async_send_command({"eco_mode": enabled})

    async def async_set_week_program(self, enabled: bool) -> HspStatus:
        """Enable or disable the weekly program."""
        return await self.async_send_command({"wprg": enabled})

    async def async_clear_error(self, code: int) -> HspStatus:
        """Mark an error as seen."""
        return await self.async_send_command({"seen_error": [{"nr": code}]})

    async def _async_get_raw(self) -> dict[str, Any]:
        """Perform a GET request and return the raw JSON object."""
        try:
            async with self._session.get(
                self.status_url, timeout=self._timeout
            ) as response:
                if response.status >= 400:
                    raise HspConnectionError(
                        f"Unexpected HTTP {response.status} from stove"
                    )
                text = await response.text()
        except HspError:
            raise
        except TimeoutError as err:
            raise HspConnectionError("Timeout while contacting stove") from err
        except aiohttp.ClientError as err:
            raise HspConnectionError(str(err)) from err

        try:
            data = json.loads(text)
        except ValueError as err:
            raise HspParseError("Invalid JSON received from stove") from err

        if not isinstance(data, dict):
            raise HspParseError("Unexpected response received from stove")
        return data


def _calculate_pin(nonce: str, pin: str) -> str:
    """Calculate the ``X-HS-PIN`` header value."""
    pin_hash = hashlib.md5(pin.encode("utf-8"), usedforsecurity=False).hexdigest()
    return hashlib.md5(
        (nonce + pin_hash).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def _as_str(value: Any) -> str:
    """Coerce a JSON value into a string."""
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any) -> bool:
    """Coerce a JSON value into a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "on", "yes", "ja")
    return False


def _as_int(value: Any) -> int | None:
    """Coerce a JSON value into an int, tolerating numeric strings."""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    """Coerce a JSON value into a float, tolerating numeric strings."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_meta(raw: dict[str, Any]) -> HspMeta:
    """Parse the ``meta`` block."""
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    features = meta.get("wlan_features")
    return HspMeta(
        sw_version=_as_str(meta.get("sw_version")),
        hw_version=_as_str(meta.get("hw_version")),
        bootl_version=_as_str(meta.get("bootl_version")),
        wifi_sw_version=_as_str(meta.get("wifi_sw_version")),
        wifi_bootl_version=_as_str(meta.get("wifi_bootl_version")),
        sn=_as_str(meta.get("sn")),
        typ=_as_str(meta.get("typ")),
        language=_as_str(meta.get("language")),
        nonce=_as_str(meta.get("nonce")),
        ean=_as_str(meta.get("ean")),
        eco_editable=_as_bool(meta.get("eco_editable")),
        ts=_as_int(meta.get("ts")) or 0,
        rau=_as_bool(meta.get("rau")),
        wlan_features=[_as_str(item) for item in features]
        if isinstance(features, list)
        else [],
    )


def _parse_errors(value: Any) -> list[HspStoveError]:
    """Parse the ``error`` field, which may be a list, dict or empty."""
    if not value:
        return []
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []
    errors: list[HspStoveError] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        errors.append(
            HspStoveError(
                time=_as_str(entry.get("time") or entry.get("string")),
                nr=_as_int(entry.get("nr")),
            )
        )
    return errors


def _parse_week_program(value: Any) -> list[HspWeekProgramEntry]:
    """Parse the ``weekprogram`` field."""
    if not isinstance(value, list):
        return []
    schedule: list[HspWeekProgramEntry] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        schedule.append(
            HspWeekProgramEntry(
                day=_as_str(entry.get("day")),
                begin=_as_str(entry.get("begin")),
                end=_as_str(entry.get("end")),
                temperature=_as_int(entry.get("temp")),
            )
        )
    return schedule


def _parse_status(raw: dict[str, Any]) -> HspStatus:
    """Parse a raw JSON response into an :class:`HspStatus`."""
    return HspStatus(
        meta=_parse_meta(raw),
        power=_as_bool(raw.get("prg")),
        week_program=_as_bool(raw.get("wprg")),
        mode=_as_str(raw.get("mode")),
        target_temperature=_as_float(raw.get("sp_temp")),
        current_temperature=_as_float(raw.get("is_temp")),
        heating_curve=_as_int(raw.get("ht_char")),
        week_program_schedule=_parse_week_program(raw.get("weekprogram")),
        errors=_parse_errors(raw.get("error")),
        eco_mode=_as_bool(raw.get("eco_mode")),
        pgi=_as_bool(raw.get("pgi")),
        ignitions=_as_int(raw.get("ignitions")),
        on_time=_as_int(raw.get("on_time")),
        consumption=_as_int(raw.get("consumption")),
        maintenance_in=_as_int(raw.get("maintenance_in")),
        cleaning_in=_as_int(raw.get("cleaning_in")),
    )
