"""Async client for interacting with the CUPRA connected vehicle backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp


def _build_user_agent() -> str:
    """Return a descriptive user agent used for CUPRA calls."""
    return "homeassistant-cupra/0.2.0"


class CupraError(Exception):
    """Raised when the CUPRA API returns an error."""


@dataclass
class Vehicle:
    """Vehicle description returned by the CUPRA API."""

    vin: str
    name: str
    model: str


class CupraClient:
    """Handle authentication and data retrieval for CUPRA vehicles."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        *,
        region: str,
        api_base: str | None = None,
        auth_base: str | None = None,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._region = region
        self._api_base = api_base or "https://emea.bff.cariad.digital"
        self._auth_base = auth_base or "https://identity.vwgroup.io"
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._user_agent = _build_user_agent()

    async def async_login(self) -> None:
        """Authenticate against the CUPRA identity provider.

        This call is intentionally structured to make the authentication flow
        easy to adjust. CUPRA's backend is based on the Volkswagen Group
        identity stack (CARIAD), but endpoints frequently evolve. If you need
        to adapt the integration for your market, you only need to adjust the
        payload or the URL below.
        """

        token_url = f"{self._auth_base}/oidc/v1/token"
        payload = {
            "grant_type": "password",
            "username": self._email,
            "password": self._password,
            "scope": "openid profile cars",
            "client_id": "my-cupra-app",
        }

        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

        async with self._session.post(
            token_url,
            data=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            data = await self._raise_for_status(resp)
            self._token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")

        if not self._token:
            raise CupraError("Authentication succeeded but no access token was returned")

    async def async_get_vehicles(self) -> list[Vehicle]:
        """Return the vehicles associated with the current account."""
        url = f"{self._api_base}/vehicle/v1/vehicles"
        headers = self._auth_headers()

        async with self._session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await self._raise_for_status(resp)

        vehicles: list[Vehicle] = []
        for item in data.get("data", []):
            vin = item.get("vin")
            if not vin:
                continue
            vehicles.append(
                Vehicle(
                    vin=vin,
                    name=item.get("nickname") or item.get("modelName") or vin,
                    model=item.get("modelName") or "CUPRA",
                )
            )

        if not vehicles:
            raise CupraError("Nessun veicolo CUPRA trovato nell'account")

        return vehicles

    async def async_get_vehicle_status(self, vin: str) -> dict[str, Any]:
        """Return the current state for a specific vehicle."""
        url = f"{self._api_base}/vehicle/v1/vehicles/{vin}/status"
        headers = self._auth_headers()

        async with self._session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await self._raise_for_status(resp)

        payload = data.get("data") or {}
        last_updated = payload.get("lastUpdatedAt")
        if last_updated:
            try:
                payload["last_updated"] = datetime.fromisoformat(last_updated)
            except ValueError:
                payload["last_updated"] = last_updated

        return payload

    async def async_refresh_token(self) -> None:
        """Refresh an expired access token when supported by the backend."""
        if not self._refresh_token:
            raise CupraError("Unable to refresh token: refresh_token is missing")

        token_url = f"{self._auth_base}/oidc/v1/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": "my-cupra-app",
        }

        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

        async with self._session.post(
            token_url,
            data=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            data = await self._raise_for_status(resp)
            self._token = data.get("access_token")
            self._refresh_token = data.get("refresh_token", self._refresh_token)

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            raise CupraError("Richiesta non autenticata: eseguire prima il login")

        return {
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self._user_agent,
            "Accept": "application/json",
            "X-Region": self._region,
        }

    async def _raise_for_status(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        """Raise helpful errors and return the JSON payload."""
        try:
            resp.raise_for_status()
        except aiohttp.ClientResponseError as err:
            text = await resp.text()
            raise CupraError(f"{err.status} {err.message}: {text}") from err

        try:
            return await resp.json()
        except aiohttp.ContentTypeError as err:
            text = await resp.text()
            raise CupraError(f"Unexpected response from CUPRA backend: {text}") from err
