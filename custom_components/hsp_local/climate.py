"""Climate entity for the Haas+Sohn local integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HspLocalConfigEntry, HspLocalDataUpdateCoordinator
from .entity import HspLocalEntity
from .helpers import hsp_exception_handler

PARALLEL_UPDATES = 1

# Mapping of the locally reported ``mode`` value to a Home Assistant action.
MODE_TO_HVAC_ACTION: dict[str, HVACAction] = {
    "off": HVACAction.OFF,
    "aus": HVACAction.OFF,
    "standby": HVACAction.IDLE,
    "idle": HVACAction.IDLE,
    "bereit": HVACAction.IDLE,
    "heating": HVACAction.HEATING,
    "heat": HVACAction.HEATING,
    "heizen": HVACAction.HEATING,
    "burning": HVACAction.HEATING,
    "betrieb": HVACAction.HEATING,
    "ignition": HVACAction.PREHEATING,
    "igniting": HVACAction.PREHEATING,
    "preheating": HVACAction.PREHEATING,
    "pre-heating": HVACAction.PREHEATING,
    "zuendung": HVACAction.PREHEATING,
    "zunden": HVACAction.PREHEATING,
    "starting": HVACAction.PREHEATING,
    "cooling": HVACAction.IDLE,
    "abkuehlen": HVACAction.IDLE,
    "cleaning": HVACAction.IDLE,
    "reinigung": HVACAction.IDLE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HspLocalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Haas+Sohn climate entity."""
    async_add_entities([HspLocalClimateEntity(entry.runtime_data)])


class HspLocalClimateEntity(HspLocalEntity, ClimateEntity):
    """Representation of a Haas+Sohn pellet stove."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_max_temp = 30.0
    _attr_min_temp = 10.0
    _attr_name = None
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_target_temperature_step = 1.0
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: HspLocalDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self.coordinator.data.power:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action."""
        if not self.coordinator.data.power:
            return HVACAction.OFF
        mode = self.coordinator.data.mode.strip().lower()
        return MODE_TO_HVAC_ACTION.get(mode)

    @property
    def native_current_temperature(self) -> float | None:
        """Return the measured room temperature."""
        return self.coordinator.data.current_temperature

    @property
    def native_target_temperature(self) -> float | None:
        """Return the target room temperature."""
        return self.coordinator.data.target_temperature

    @hsp_exception_handler
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        await self.coordinator.client.async_set_power(hvac_mode == HVACMode.HEAT)
        await self.coordinator.async_request_refresh()

    @hsp_exception_handler
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.coordinator.client.async_set_target_temperature(temperature)
        await self.coordinator.async_request_refresh()

    @hsp_exception_handler
    async def async_turn_on(self) -> None:
        """Turn the stove on."""
        await self.coordinator.client.async_set_power(True)
        await self.coordinator.async_request_refresh()

    @hsp_exception_handler
    async def async_turn_off(self) -> None:
        """Turn the stove off."""
        await self.coordinator.client.async_set_power(False)
        await self.coordinator.async_request_refresh()
