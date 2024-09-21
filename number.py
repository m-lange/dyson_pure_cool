"""Platform for number integration."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import DysonEntity
from .const import DOMAIN
from .dyson import DysonPureCool

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Dyson Pure Cool numbner from a config entry."""

    device = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    async_add_entities([
        DysonOscillateLowerEntity(coordinator, device),
        DysonOscillateUpperEntity(coordinator, device)
    ])


class DysonOscillateLowerEntity(NumberEntity, DysonEntity):
    """Representation of a dyson number entity for the lower boundary of the oscillation."""

    _attr_entity_category = EntityCategory.CONFIG


    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool):
        """Initialize a dyson number entity for the lower boundary of the oscillation."""
        super().__init__(coordinator, device, "Oscillation lower boundary", "osal")

        self._attr_mode =  NumberMode.BOX
        self._attr_device_class = None
        self._attr_native_min_value = 5
        self._attr_native_max_value = 355
        self._attr_native_step = 1
        self._attr_icon = "mdi:rotate-left"


    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return self._device.oscillate_lower


    def set_native_value(self, value: float) -> None:
        """Update the current value."""

        self._device.oscillate(
            self._device.is_on,
            int(value),
            self._device.oscillate_upper
        )


    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.is_on and self._device.oscillating


class DysonOscillateUpperEntity(NumberEntity, DysonEntity):
    """Representation of a dyson number entity for the upper boundary of the oscillation."""

    _attr_entity_category = EntityCategory.CONFIG


    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool):
        """Initialize a dyson number entity for the upper boundary of the oscillation."""
        super().__init__(coordinator, device, "Oscillation upper boundary", "osau")

        self._attr_mode =  NumberMode.BOX
        self._attr_device_class = None
        self._attr_native_min_value = 5
        self._attr_native_max_value = 355
        self._attr_native_step = 1
        self._attr_icon = "mdi:rotate-right"


    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return self._device.oscillate_upper


    def set_native_value(self, value: float) -> None:
        """Update the current value."""

        self._device.oscillate(
            self._device.is_on,
            self._device.oscillate_lower,
            int(value)
        )


    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.is_on and self._device.oscillating
