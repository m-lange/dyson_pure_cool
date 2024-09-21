"""Platform for sensor integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import DysonEntity
from .const import DOMAIN
from .dyson import DysonPureCool

_LOGGER = logging.getLogger(__name__)



SENSOR_TYPES = [
    {
        "id": "temperature",
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
        "suggested_display_precision": 1
    },
    {
        "id": "humidity",
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "native_unit_of_measurement": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent"
    },
    {
        "id": "pm25",
        "name": "Particulate matter (PM2.5)",
        "device_class": SensorDeviceClass.PM25,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:blur-radial"
    },
    {
        "id": "pm10",
        "name": "Particulate matter (PM10)",
        "device_class": SensorDeviceClass.PM10,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:blur-radial"
    },
    {
        "id": "va10",
        "name": "Volatile organic compounds",
        "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:molecule"
    },
    {
        "id": "noxl",
        "name": "Nitrogen dioxide and other oxidising gases",
        "device_class": SensorDeviceClass.NITROGEN_DIOXIDE,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:molecule"
    },
    {
        "id": "hflr",
        "name": "HEPA filter life",
        "native_unit_of_measurement": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:alpha-h-box-outline"
    },
    {
        "id": "cflr",
        "name": "Carbon filter life",
        "native_unit_of_measurement": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:alpha-c-box-outline"
    }

]



async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Dyson Pure Cool sensors from a config entry."""

    device = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    async_add_entities(
        DysonSensorEntity(coordinator, device, data) for data in SENSOR_TYPES
    )


class DysonSensorEntity(SensorEntity, DysonEntity):
    """Representation of a dyson sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool, description: dict[str, Any]):
        """Initialize a dyson sensor entity."""
        super().__init__(coordinator, device, description["name"], description["id"])

        for key, value in description.items():
            if key in ["name", "id"]:
                continue

            name = f"_attr_{key}"
            setattr(self, name, value)


    @property
    def native_value(self):
        """Return the value reported by the sensor."""

        match self._id:
            case "temperature":
                return self._device.temperature
            case "humidity":
                return self._device.humidity
            case "pm25":
                return self._device.pm25
            case "pm10":
                return self._device.pm10
            case "va10":
                return self._device.voc
            case "noxl":
                return self._device.nox
            case "hflr":
                return self._device.hepa_filter_life
            case "cflr":
                return self._device.carbon_filter_life

        return None
