"""Base entity for the Haas+Sohn local integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HspLocalDataUpdateCoordinator


class HspLocalEntity(CoordinatorEntity[HspLocalDataUpdateCoordinator]):
    """Defines a base Haas+Sohn entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HspLocalDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        info = coordinator.data
        serial = info.meta.sn or coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="Haas+Sohn",
            model=info.meta.typ or None,
            name=f"Haas+Sohn {info.meta.typ}".strip() or "Haas+Sohn Stove",
            sw_version=info.meta.sw_version or None,
            hw_version=info.meta.hw_version or None,
            configuration_url=coordinator.client.base_url,
        )
