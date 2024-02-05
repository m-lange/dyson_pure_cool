"""Provides functionality to interact Dyson Pure Cool fans."""

from __future__ import annotations
from collections.abc import Mapping

import math
import logging
from typing import Any, Optional
import voluptuous as vol

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.util.percentage import int_states_in_range, ranged_value_to_percentage, percentage_to_ranged_value

from . import DysonEntity
from .dyson import DysonPureCool

from .const import (
    DOMAIN,
    SPEED_RANGE,
    DYSON_AUTO_MODE,
    ATTR_OSCILLATE_LOWER,
    ATTR_OSCILLATE_UPPER,
    ATTR_SLEEP_TIMER
)

_LOGGER = logging.getLogger(__name__)



async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Dyson Pure Cool fan from a config entry"""

    device = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    async_add_entities([DysonFanEntity(coordinator, device)])

    # Register entity services in the platforms
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "set_oscillate",
        {
            vol.Optional("osal"): vol.All(cv.positive_int, vol.Range(min=5, max=355)),
            vol.Optional("osau"): vol.All(cv.positive_int, vol.Range(min=5, max=355)),
        },
        "set_oscillate"
    )
    platform.async_register_entity_service(
        "set_sleep_timer",
        {
            vol.Optional("sltm"): vol.All(cv.positive_int, vol.Range(min=0, max=540))
        },
        "set_sleep_timer"
    )


class DysonFanEntity(FanEntity, DysonEntity):
    """Representation of a dyson fan entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool):
        super().__init__(coordinator, device, None, None)

        self._attr_icon = "mdi:fan"


    @property
    def current_direction(self) -> str:
        """Return the current direction of the fan"""
        return self._device.current_direction
    

    @property
    def is_on(self) -> bool:
        """Return true if the entity is on"""
        return self._device.is_on
    

    @property
    def oscillating(self) -> bool:
        """Return true if the fan is oscillating"""
        return self._device.oscillating


    @property
    def percentage(self) -> int:
        """Get the speed percentage of the fan."""
        if self._device.speed is None: return 0
        if not self._device.is_on: return 0

        return ranged_value_to_percentage(SPEED_RANGE, int(self._device.speed))
    

    @property 
    def speed_count(self) -> int:
        """The number of speeds the fan supports"""
        return int_states_in_range(SPEED_RANGE)
    

    @property
    def supported_features(self) -> int:
        """Flag supported features"""
        return FanEntityFeature.DIRECTION | FanEntityFeature.OSCILLATE | FanEntityFeature.PRESET_MODE | FanEntityFeature.SET_SPEED
    

    @property
    def preset_mode(self) -> str:
        """Return the current preset_mode"""
        if self._device.preset_mode == DYSON_AUTO_MODE: return DYSON_AUTO_MODE
        return None


    @property
    def preset_modes(self) -> list:
        """Get the list of available preset_modes"""
        return [ DYSON_AUTO_MODE ]
    

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes"""
        return {
            ATTR_OSCILLATE_LOWER: self._device.oscillate_lower,
            ATTR_OSCILLATE_UPPER: self._device.oscillate_upper,
            ATTR_SLEEP_TIMER: self._device.sleep_timer
        }
    

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""

        self._device.set_direction(direction)


    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""

        self._device.set_preset_mode(preset_mode)
    

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""

        if percentage == 0: self._device.turn_off()
        else:
            speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
            self._device.set_speed(speed)

        return
    

    def turn_on(self, speed: Optional[str] = None, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan."""

        if preset_mode: self.set_preset_mode(preset_mode)
        if percentage: self.set_percentage(percentage)

        self._device.turn_on()


    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""

        self._device.turn_off()


    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        
        self._device.oscillate(oscillating, 5, 355)


    def set_oscillate(self, **kwargs: Any) -> None:
        """Oscillate the fan."""

        osal = kwargs.get('osal')
        osau = kwargs.get('osau')
        self._device.oscillate(True, osal, osau)


    def set_sleep_timer(self, sltm: int) -> None:
        """Set sleep timer"""

        self._device.set_sleep_timer(sltm)