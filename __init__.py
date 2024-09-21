"""The Dyson Pure Cool integration."""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_HOST, CONF_SERIAL, DOMAIN
from .coordinator import DysonUpdateCoordinator
from .dyson import DysonPureCool
from .exceptions import CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.FAN, Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Required(CONF_SERIAL): cv.string,
            vol.Required(CONF_CREDENTIAL): cv.string,
            vol.Optional(CONF_DEVICE_TYPE, default="438"): cv.string,
            vol.Optional(CONF_HOST, default=""): cv.string
        })
    },
    extra = vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Dyson Pure Cool from configuration file."""

    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN]
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dyson Pure Cool from a config entry."""

    try:
        serial = entry.data[CONF_SERIAL]
        credential = entry.data[CONF_CREDENTIAL]
        device_type = entry.data[CONF_DEVICE_TYPE]
        host = entry.data[CONF_HOST]

        device = DysonPureCool(serial, credential, device_type)

        _LOGGER.debug("Trying to connect to Dyson Pure Cool (%s) %s", device_type, serial)
        device.connect(host)

        hass.config_entries.async_update_entry(
            entry,
            options={"rhtm": device.continuous_monitoring}
        )

        # Store an instance of the "connecting" class that does the work of speaking
        # with your actual devices.
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = device

        coordinator = DysonUpdateCoordinator(hass, device)
        hass.data[DOMAIN][f"{entry.entry_id}_coordinator"] = coordinator

        await coordinator.async_config_entry_first_refresh()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register an update listener to the config entry that will be called when the entry is updated.
        entry.async_on_unload(entry.add_update_listener(async_update_listener))

    except InvalidAuth:
        _LOGGER.error("Connection refused - bad username or password")
        raise ConfigEntryNotReady from None
    except CannotConnect:
        _LOGGER.error("Connection refused")
        raise ConfigEntryNotReady from None

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""

    rhtm = entry.options.get("rhtm")
    device: DysonPureCool = hass.data[DOMAIN][entry.entry_id]
    device.set_continuous_monitoring(rhtm)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok



class DysonEntity(CoordinatorEntity, Entity):
    """Representation of a dyson entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool, name: str, id: str):
        """Initialize a dyson entity."""

        super().__init__(coordinator)

        self._device = device
        self._coordinator = coordinator
        self._name = name
        self._id = id


    @property
    def device_info(self) -> dict:
        """Return device specific attributes."""
        return {
            "identifiers": {(DOMAIN, self._device.serial)},
            "name": "Dyson Pure Cool",
            "manufacturer": "Dyson",
            "model": self._device.serial
        }


    async def async_added_to_hass(self) -> None:
        """Finish adding an entity to a platform."""
        self._device.add_update_listener(self._handle_device_update)


    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self._name is None:
            return "Dyson Pure Cool"
        return f"Dyson Pure Cool {self._name}"


    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        if self._id is None:
            return self._device.serial
        return f"{self._device.serial}-{self._id}"


    @callback
    def _handle_device_update(self, device: DysonPureCool, data: dict) -> None:
        """Handle a state-change message from the device."""
        self.schedule_update_ha_state()


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

