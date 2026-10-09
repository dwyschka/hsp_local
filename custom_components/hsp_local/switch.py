"""Switch entities for the Haas+Sohn local integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HspLocalConfigEntry, HspLocalDataUpdateCoordinator
from .entity import HspLocalEntity
from .helpers import hsp_exception_handler
from .hsp_client import HspClient, HspStatus

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class HspSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Haas+Sohn switch entity."""

    is_on_fn: Callable[[HspStatus], bool]
    turn_on_fn: Callable[[HspClient], Awaitable[Any]]
    turn_off_fn: Callable[[HspClient], Awaitable[Any]]
    has_fn: Callable[[HspStatus], bool] = lambda _: True
    attr_fn: Callable[[HspStatus], dict[str, Any]] | None = None


SWITCHES: tuple[HspSwitchEntityDescription, ...] = (
    HspSwitchEntityDescription(
        key="power",
        translation_key="power",
        is_on_fn=lambda status: status.power,
        turn_on_fn=lambda client: client.async_set_power(True),
        turn_off_fn=lambda client: client.async_set_power(False),
    ),
    HspSwitchEntityDescription(
        key="week_program",
        translation_key="week_program",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda status: status.week_program,
        turn_on_fn=lambda client: client.async_set_week_program(True),
        turn_off_fn=lambda client: client.async_set_week_program(False),
        attr_fn=lambda status: {
            "schedule": [
                {
                    "day": entry.day,
                    "begin": entry.begin,
                    "end": entry.end,
                    "temperature": entry.temperature,
                }
                for entry in status.week_program_schedule
            ]
        },
    ),
    HspSwitchEntityDescription(
        key="eco_mode",
        translation_key="eco_mode",
        entity_category=EntityCategory.CONFIG,
        has_fn=lambda status: status.meta.eco_editable,
        is_on_fn=lambda status: status.eco_mode,
        turn_on_fn=lambda client: client.async_set_eco_mode(True),
        turn_off_fn=lambda client: client.async_set_eco_mode(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HspLocalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Haas+Sohn switch entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        HspSwitchEntity(coordinator=coordinator, description=description)
        for description in SWITCHES
        if description.has_fn(coordinator.data)
    )


class HspSwitchEntity(HspLocalEntity, SwitchEntity):
    """Defines a Haas+Sohn switch entity."""

    entity_description: HspSwitchEntityDescription

    def __init__(
        self,
        coordinator: HspLocalDataUpdateCoordinator,
        description: HspSwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    @hsp_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()

    @hsp_exception_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()
