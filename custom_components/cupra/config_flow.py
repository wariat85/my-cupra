"""Config flow for the CUPRA integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import CupraClient, CupraError
from .const import (
    CONF_REGION,
    CONF_VEHICLE_MODEL,
    CONF_VEHICLE_NAME,
    CONF_VIN,
    DEFAULT_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    REGIONS,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS),
    }
)


class CupraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CUPRA vehicles."""

    VERSION = 1

    def __init__(self) -> None:
        self._vehicles: dict[str, dict[str, str]] = {}
        self._credentials: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=USER_SCHEMA)

        errors: dict[str, str] = {}

        client = CupraClient(
            self.hass.helpers.aiohttp_client.async_get_clientsession(),
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            region=user_input[CONF_REGION],
        )

        try:
            await client.async_login()
            vehicles = await client.async_get_vehicles()
        except CupraError:
            errors["base"] = "cannot_connect"
            return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)

        if not vehicles:
            errors["base"] = "no_vehicle"
            return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)

        if len(vehicles) == 1:
            vehicle = vehicles[0]
            return await self._create_entry(user_input, vehicle.vin, vehicle.name, vehicle.model)

        self._credentials = user_input
        self._vehicles = {vehicle.vin: {"name": vehicle.name, "model": vehicle.model} for vehicle in vehicles}
        return await self.async_step_select_vehicle()

    async def async_step_select_vehicle(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="select_vehicle",
                data_schema=vol.Schema({vol.Required(CONF_VIN): vol.In(self._vehicles)}),
            )

        selected_vin = user_input[CONF_VIN]
        vehicle_info = self._vehicles[selected_vin]
        return await self._create_entry(
            self._credentials,
            selected_vin,
            vehicle_info["name"],
            vehicle_info["model"],
        )

    async def _create_entry(
        self, credentials: dict[str, Any], vin: str, vehicle_name: str, vehicle_model: str
    ) -> FlowResult:
        await self.async_set_unique_id(vin)
        self._abort_if_unique_id_configured()

        data = {
            CONF_USERNAME: credentials[CONF_USERNAME],
            CONF_PASSWORD: credentials[CONF_PASSWORD],
            CONF_REGION: credentials[CONF_REGION],
            CONF_VIN: vin,
            CONF_VEHICLE_NAME: vehicle_name,
            CONF_VEHICLE_MODEL: vehicle_model,
        }

        options = {"scan_interval": int(DEFAULT_SCAN_INTERVAL.total_seconds())}
        return self.async_create_entry(title=vehicle_name, data=data, options=options)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return CupraOptionsFlow(config_entry)


class CupraOptionsFlow(config_entries.OptionsFlow):
    """Handle options for CUPRA vehicles."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "scan_interval",
                        default=self.config_entry.options.get(
                            "scan_interval", int(DEFAULT_SCAN_INTERVAL.total_seconds())
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60)),
                }
            ),
        )
