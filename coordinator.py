"""DataUpdateCoordinator for the Dyson Pure Cool integration."""

import asyncio
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .dyson import DysonPureCool

_LOGGER = logging.getLogger(__name__)


class DysonUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from dyson device."""

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
        async with asyncio.timeout(10):
            try:
                self._device.request_envionment_data()
            except ValueError as e:
                raise UpdateFailed("Failed to request environmental data") from e
