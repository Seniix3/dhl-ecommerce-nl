"""Client for the (unofficial) my.dhlecommerce.nl consumer parcel API.

Auth flow (reverse-engineered):
  1. POST /api/user/login            -> sets cookies incl. XSRF-TOKEN
  2. GET  /receiver-parcel-api/parcels
         with all cookies + header  X-XSRF-TOKEN: <XSRF-TOKEN cookie value>

The parcels endpoint is CSRF-protected: sending the session cookies alone
returns HTTP 401. You must echo the XSRF-TOKEN cookie back in the
X-XSRF-TOKEN request header (double-submit cookie pattern).
"""
from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE = "https://my.dhlecommerce.nl"
LOGIN_URL = f"{BASE}/api/user/login"
PARCELS_URL = f"{BASE}/receiver-parcel-api/parcels?tab=incoming"

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
_TIMEOUT = aiohttp.ClientTimeout(total=45)


class DhlAuthError(Exception):
    """Raised when login fails or the session is not authorized."""


class DhlApiError(Exception):
    """Raised for transient/technical problems talking to DHL."""


class DhlEcommerceApi:
    """Minimal async client that returns the list of parcels."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password

    async def async_get_parcels(self) -> list[dict]:
        """Log in and return the list of parcels (raises on failure)."""
        # A fresh session (own cookie jar) per poll keeps things simple and
        # transparently handles token expiry.
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            await self._login(session)
            xsrf = self._xsrf_token(session)
            if not xsrf:
                raise DhlAuthError(
                    "Login succeeded but no XSRF-TOKEN cookie was returned; "
                    "DHL may have changed the login flow."
                )
            return await self._fetch_parcels(session, xsrf)

    async def _login(self, session: aiohttp.ClientSession) -> None:
        payload = {"email": self._email, "password": self._password}
        headers = {"Accept": "application/json", "User-Agent": _UA}
        try:
            async with session.post(
                LOGIN_URL, json=payload, headers=headers
            ) as resp:
                await resp.read()
                if resp.status in (401, 403):
                    raise DhlAuthError("Invalid DHL e-mail or password.")
                if resp.status not in (200, 204):
                    raise DhlApiError(f"Login returned HTTP {resp.status}.")
        except aiohttp.ClientError as err:
            raise DhlApiError(f"Login connection error: {err}") from err

    @staticmethod
    def _xsrf_token(session: aiohttp.ClientSession) -> str | None:
        for cookie in session.cookie_jar:
            if cookie.key == "XSRF-TOKEN":
                return cookie.value
        return None

    async def _fetch_parcels(
        self, session: aiohttp.ClientSession, xsrf: str
    ) -> list[dict]:
        headers = {
            "Accept": "application/json",
            "User-Agent": _UA,
            "X-XSRF-TOKEN": xsrf,
        }
        try:
            async with session.get(PARCELS_URL, headers=headers) as resp:
                if resp.status in (401, 403):
                    raise DhlAuthError(
                        f"Parcels request was not authorized (HTTP {resp.status})."
                    )
                if resp.status != 200:
                    raise DhlApiError(
                        f"Parcels request returned HTTP {resp.status}."
                    )
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise DhlApiError(f"Parcels connection error: {err}") from err
        except ValueError as err:
            raise DhlApiError(f"Parcels response was not valid JSON: {err}") from err

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("parcels", "items", "data", "results"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []
