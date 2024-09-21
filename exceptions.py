"""Exceptions for the Dyson Pure Cool integration."""

from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""



class DysonCannotConnect(Exception):
    """Error to indicate we cannot connect."""

class DysonInvalidAuth(Exception):
    """Error to indicate there is invalid auth."""

class DysonNotConnected(Exception):
    """Error to indicate not connected."""
