"""DataUpdateCoordinator for the Dyson Pure Cool integration."""

from datetime import timedelta
import logging

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .dyson import DysonPureCool

_LOGGER = logging.getLogger(__name__)


class DysonUpdateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, device: DysonPureCool):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="environmental",
            update_interval=timedelta(seconds=5),
        )
        self._device = device


    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        async with async_timeout.timeout(10): 
            try:
                self._device.request_envionment_data()
            except Exception:
                raise UpdateFailed("Failed to request environmental data")
