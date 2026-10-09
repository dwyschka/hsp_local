"""Diagnostics support for the Haas+Sohn local integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PIN
from .coordinator import HspLocalConfigEntry

TO_REDACT = {CONF_PIN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HspLocalConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "status": asdict(coordinator.data),
        "last_update_success": coordinator.last_update_success,
    }
