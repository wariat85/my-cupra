"""Coordinator for CUPRA data updates."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CupraClient, CupraError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CupraDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Shared CUPRA data update handling."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: CupraClient,
        vin: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._client = client
        self._vin = vin

    async def _async_update_data(self) -> dict:
        try:
            return await self._client.async_get_vehicle_status(self._vin)
        except CupraError as err:
            raise UpdateFailed(f"Aggiornamento CUPRA fallito: {err}") from err
