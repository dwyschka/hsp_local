"""Sensor entities for the Haas+Sohn local integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HspLocalConfigEntry, HspLocalDataUpdateCoordinator
from .entity import HspLocalEntity
from .hsp_client import HspStatus

PARALLEL_UPDATES = 0


def _error_state(status: HspStatus) -> str:
    """Return the current error as a sensor state."""
    if not status.errors:
        return "none"
    return str(status.errors[0].nr if status.errors[0].nr is not None else "unknown")


def _error_attributes(status: HspStatus) -> dict[str, Any]:
    """Return extra attributes for the error sensor."""
    if not status.errors:
        return {"code": None, "count": 0}
    first = status.errors[0]
    return {
        "code": first.nr,
        "time": first.time or None,
        "count": len(status.errors),
        "errors": [{"code": err.nr, "time": err.time or None} for err in status.errors],
    }


@dataclass(frozen=True, kw_only=True)
class HspSensorEntityDescription(SensorEntityDescription):
    """Describes a Haas+Sohn sensor entity."""

    value_fn: Callable[[HspStatus], Any]
    attr_fn: Callable[[HspStatus], dict[str, Any]] | None = None


SENSORS: tuple[HspSensorEntityDescription, ...] = (
    HspSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda status: status.current_temperature,
    ),
    HspSensorEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda status: status.target_temperature,
    ),
    HspSensorEntityDescription(
        key="mode",
        translation_key="mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.mode or None,
    ),
    HspSensorEntityDescription(
        key="error",
        translation_key="error",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_error_state,
        attr_fn=_error_attributes,
    ),
    HspSensorEntityDescription(
        key="ignitions",
        translation_key="ignitions",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.ignitions,
    ),
    HspSensorEntityDescription(
        key="on_time",
        translation_key="on_time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.on_time,
    ),
    HspSensorEntityDescription(
        key="consumption",
        translation_key="consumption",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.consumption,
    ),
    HspSensorEntityDescription(
        key="maintenance_in",
        translation_key="maintenance_in",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.maintenance_in,
    ),
    HspSensorEntityDescription(
        key="cleaning_in",
        translation_key="cleaning_in",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: (
            status.cleaning_in / 60 if status.cleaning_in is not None else None
        ),
    ),
    HspSensorEntityDescription(
        key="heating_curve",
        translation_key="heating_curve",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda status: status.heating_curve,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HspLocalConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Haas+Sohn sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        HspSensorEntity(coordinator=coordinator, description=description)
        for description in SENSORS
    )


class HspSensorEntity(HspLocalEntity, SensorEntity):
    """Defines a Haas+Sohn sensor entity."""

    entity_description: HspSensorEntityDescription

    def __init__(
        self,
        coordinator: HspLocalDataUpdateCoordinator,
        description: HspSensorEntityDescription,
    ) -> None:
        """Initialize the sensor entity."""
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
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
