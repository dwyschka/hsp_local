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

type HspLocalConfigEntry = ConfigEntry[HspLocalDataUpdateCoordinator]


class HspLocalDataUpdateCoordinator(DataUpdateCoordinator[HspStatus]):
    """Class to manage fetching Haas+Sohn stove data (locally)."""

    config_entry: HspLocalConfigEntry

    def __init__(self, hass: HomeAssistant, entry: HspLocalConfigEntry) -> None:
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
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
        except HspError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="unknown_error",
                translation_placeholders={"error": str(err)},
            ) from err
