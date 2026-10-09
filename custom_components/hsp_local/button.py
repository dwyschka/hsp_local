"""Button entities for the Haas+Sohn local integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HspLocalConfigEntry, HspLocalDataUpdateCoordinator
from .entity import HspLocalEntity
from .helpers import hsp_exception_handler

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HspLocalConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Haas+Sohn button entities."""
    async_add_entities([HspLocalClearErrorButton(entry.runtime_data)])


class HspLocalClearErrorButton(HspLocalEntity, ButtonEntity):
    """Button that acknowledges the active error on the stove."""

    _attr_translation_key = "clear_error"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: HspLocalDataUpdateCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_clear_error"

    @hsp_exception_handler
    async def async_press(self) -> None:
        """Acknowledge the active error, if any."""
        errors = self.coordinator.data.errors
        if not errors:
            return
        code = errors[0].nr
        if code is None:
            return
        await self.coordinator.client.async_clear_error(code)
        await self.coordinator.async_request_refresh()
