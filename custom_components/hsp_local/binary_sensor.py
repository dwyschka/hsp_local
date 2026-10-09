"""Binary sensor entities for the Haas+Sohn local integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HspLocalConfigEntry, HspLocalDataUpdateCoordinator
from .entity import HspLocalEntity
from .hsp_client import HspStatus

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class HspBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Haas+Sohn binary sensor entity."""

    is_on_fn: Callable[[HspStatus], bool]


BINARY_SENSORS: tuple[HspBinarySensorEntityDescription, ...] = (
    HspBinarySensorEntityDescription(
        key="week_program_active",
        translation_key="week_program_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda status: status.week_program,
    ),
    HspBinarySensorEntityDescription(
        key="pgi",
        translation_key="pgi",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        is_on_fn=lambda status: status.pgi,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HspLocalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Haas+Sohn binary sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        HspBinarySensorEntity(coordinator=coordinator, description=description)
        for description in BINARY_SENSORS
    )


class HspBinarySensorEntity(HspLocalEntity, BinarySensorEntity):
    """Defines a Haas+Sohn binary sensor entity."""

    entity_description: HspBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: HspLocalDataUpdateCoordinator,
        description: HspBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        return self.entity_description.is_on_fn(self.coordinator.data)
