"""Platform for switch integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import DysonEntity
from .const import DOMAIN, DYSON_AUTO_MODE, DYSON_AUTO_NIGHT_MODE, DYSON_NIGHT_MODE
from .dyson import DysonPureCool

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Dyson Pure Cool switch from a config entry."""

    device = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    async_add_entities([
        DysonNightModeSwitchEntity(coordinator, device)
    ])



class DysonNightModeSwitchEntity(SwitchEntity, DysonEntity):
    """Representation of a dyson switch entity."""

    _attr_entity_category = EntityCategory.CONFIG


    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool):
        """Initialize a dyson switch entity."""
        super().__init__(coordinator, device, "Night mode", "nmod")


    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if self._device.preset_mode in [DYSON_NIGHT_MODE, DYSON_AUTO_NIGHT_MODE]:
            return "mdi:shield-moon"
        return "mdi:shield-moon-outline"


    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._device.preset_mode in [DYSON_NIGHT_MODE, DYSON_AUTO_NIGHT_MODE]


    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if self._device.preset_mode == DYSON_AUTO_MODE:
            self._device.set_preset_mode(DYSON_AUTO_NIGHT_MODE)
        else:
            self._device.set_preset_mode(DYSON_NIGHT_MODE)


    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if self._device.preset_mode == DYSON_AUTO_NIGHT_MODE:
            self._device.set_preset_mode(DYSON_AUTO_MODE)
        else:
            self._device.set_preset_mode(None)
