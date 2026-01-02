"""CUPRA custom component entrypoint."""

from __future__ import annotations

import logging

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import CupraClient, CupraError
from .const import CONF_REGION, CONF_VIN, DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import CupraDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


def _client_from_config_entry(hass: HomeAssistant, entry: ConfigEntry) -> CupraClient:
    session = hass.helpers.aiohttp_client.async_get_clientsession()
    return CupraClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        region=entry.data[CONF_REGION],
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = _client_from_config_entry(hass, entry)

    try:
        await client.async_login()
        scan_interval_seconds = entry.options.get("scan_interval")
        update_interval = (
            timedelta(seconds=scan_interval_seconds)
            if isinstance(scan_interval_seconds, (int, float))
            else DEFAULT_SCAN_INTERVAL
        )
        coordinator = CupraDataUpdateCoordinator(
            hass,
            client=client,
            vin=entry.data[CONF_VIN],
            update_interval=update_interval,
        )
        await coordinator.async_config_entry_first_refresh()
    except CupraError as err:
        raise ConfigEntryNotReady(f"Impossibile connettersi a CUPRA: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration when removed from Home Assistant."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
