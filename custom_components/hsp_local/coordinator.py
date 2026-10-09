"""DataUpdateCoordinator for the Haas+Sohn local integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PIN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)
from .hsp_client import HspClient, HspConnectionError, HspError, HspStatus

# Type alias for the config entry used by this integration.
HspLocalConfigEntry = ConfigEntry


class HspLocalDataUpdateCoordinator(DataUpdateCoordinator[HspStatus]):
    """Class to manage fetching Haas+Sohn stove data (locally)."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.client = HspClient(
            session=async_get_clientsession(hass),
            host=entry.data[CONF_HOST],
            pin=entry.data[CONF_PIN],
        )
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> HspStatus:
        """Fetch the latest status from the stove."""
        try:
            return await self.client.async_get_status()
        except HspConnectionError as err:
            raise UpdateFailed(f"Error communicating with the stove: {err}") from err
        except HspError as err:
            raise UpdateFailed(f"Unexpected error communicating with the stove: {err}") from err
