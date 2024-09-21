"""Config flow for Dyson Pure Cool integration."""

from __future__ import annotations

import logging
import socket
from typing import Any

import voluptuous as vol

from homeassistant.components import zeroconf
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CREDENTIAL,
    CONF_DEVICE_TYPE,
    CONF_HOST,
    CONF_SERIAL,
    DOMAIN,
    ZEROCONF_TYPE,
)
from .dyson import DysonPureCool
from .exceptions import CannotConnect, DysonCannotConnect, DysonInvalidAuth, InvalidAuth

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    try:
        if CONF_HOST not in data or len(data[CONF_HOST]) == 0:
            zeroconf_instance = await zeroconf.async_get_instance(hass)

            result = await hass.async_add_executor_job(
                resolve_host,
                data[CONF_SERIAL],
                data[CONF_DEVICE_TYPE],
                zeroconf_instance,
            )

            data[CONF_HOST] = result

        device = DysonPureCool(data[CONF_SERIAL], data[CONF_CREDENTIAL], data[CONF_DEVICE_TYPE])
        _LOGGER.debug("Trying to connect to Dyson Pure Cool (%s) %s", data[CONF_DEVICE_TYPE], data[CONF_SERIAL])
        device.connect(data[CONF_HOST])

    except DysonInvalidAuth as e:
        _LOGGER.error(str(e))
        raise InvalidAuth from e
    except DysonCannotConnect as e:
        _LOGGER.error(str(e))
        raise CannotConnect from e
    except Exception as e:
        _LOGGER.error(str(e))
        raise CannotConnect from e

    return {
        "title": f"Dyson Pure Cool ({data[CONF_SERIAL]})",
        CONF_SERIAL: data[CONF_SERIAL],
        CONF_CREDENTIAL: data[CONF_CREDENTIAL],
        CONF_DEVICE_TYPE: data[CONF_DEVICE_TYPE],
        CONF_HOST: data[CONF_HOST]
    }


def resolve_host(serial: str, device_type: str, zeroconf_instance: zeroconf.HaZeroconf) -> dict[str, str | None]:
    """Resolce a service with a known name."""

    _LOGGER.debug("Trying to get address of Dyson Pure Cool (%s) %s", device_type, serial)

    info = zeroconf_instance.get_service_info(ZEROCONF_TYPE, f"{device_type}_{serial}.{ZEROCONF_TYPE}")

    if not info:
        _LOGGER.debug("Could not get information about Dyson Pure Cool (%s) %s", device_type, serial)
        return None

    return socket.inet_ntoa(info.addresses[0])



class DysonConfigFlow(ConfigFlow, domain = DOMAIN):
    """Handle a config flow for Dyson Pure Cool."""

    VERSION = 1


    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return DysonOptionsFlowHandler(config_entry)


    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_schema: dict[type[vol.Required|vol.Optional], type[str]] | None = None


    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by user."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(user_input[CONF_SERIAL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"

            except InvalidAuth:
                errors["base"] = "invalid_auth"


        data = self.discovery_schema or {
            vol.Required(CONF_SERIAL): str,
            vol.Required(CONF_CREDENTIAL): str,
            vol.Required(CONF_DEVICE_TYPE, default="438"): str,
            vol.Optional(CONF_HOST): str
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data),
            errors=errors,
        )


    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        """Handle a flow initialized by Zeroconf discovery."""

        host = discovery_info.host
        name = discovery_info.name.removesuffix(f".{ZEROCONF_TYPE}")

        device_type = name.split("_")[0]
        serial = name.split("_")[1]

        _LOGGER.debug("Discovered Dyson Pure Cool (%s) with serial number %s at %s", device_type, serial, host)

        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self.context["title_placeholders"] = {CONF_SERIAL: serial}

        self.discovery_schema = {
            vol.Required(CONF_SERIAL, default=serial): str,
            vol.Required(CONF_CREDENTIAL): str,
            vol.Required(CONF_DEVICE_TYPE, default=device_type): str,
            vol.Optional(CONF_HOST, default=host): str
        }

        return await self.async_step_user()


    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Handle a flow initialized by import from configuration file."""

        info = await validate_input(self.hass, user_input)

        await self.async_set_unique_id(user_input[CONF_SERIAL])
        self._abort_if_unique_id_configured(updates={
            CONF_HOST: user_input[CONF_HOST],
            CONF_CREDENTIAL: user_input[CONF_CREDENTIAL],
            CONF_DEVICE_TYPE: user_input[CONF_DEVICE_TYPE]
        })

        return self.async_create_entry(title=info["title"], data=user_input)



class DysonOptionsFlowHandler(OptionsFlow):
    """Handle a options flow for Dyson Pure Cool."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry


    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {
            vol.Required('rhtm', default=self.config_entry.options.get("rhtm")): bool
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(data)
        )
