"""Platform for sensor integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


from homeassistant.const import (
    TEMP_CELSIUS,
    PERCENTAGE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
)

from . import DysonEntity
from .dyson import DysonPureCool
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = [
    { 
        "id": "temperature",
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": TEMP_CELSIUS,
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
    },
    {  
        "id": "aqi",
        "name": "Air Quality Index",
        "device_class": SensorDeviceClass.AQI,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:alpha-a-box-outline"
    }

]
    


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Dyson Pure Cool sensors from a config entry"""

    device = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    async_add_entities(
        DysonSensorEntity(coordinator, device, data) for data in SENSOR_TYPES
    )


class DysonSensorEntity(SensorEntity, DysonEntity):
    """Representation of a dyson sensor entity."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonPureCool, description: dict[str, Any]):
        super().__init__(coordinator, device, description["name"], description["id"])

        for key, value in description.items():
            if key in ["name", "id"]: continue

            name = f"_attr_{key}"
            setattr(self, name, value)


    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        
        if self._id == "temperature": return self._device.temperature
        if self._id == "humidity": return self._device.humidity
        if self._id == "pm25": return self._device.pm25
        if self._id == "pm10": return self._device.pm10
        if self._id == "va10": return self._device.voc
        if self._id == "noxl": return self._device.nox
        if self._id == "hflr": return self._device.hepa_filter_life
        if self._id == "cflr": return self._device.carbon_filter_life
        if self._id == "aqi": return 3

        return None
