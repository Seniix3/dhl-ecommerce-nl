"""DataUpdateCoordinator for DHL eCommerce (NL)."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DhlApiError, DhlAuthError, DhlEcommerceApi
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DhlDataUpdateCoordinator(DataUpdateCoordinator[list[dict]]):
    """Fetches the parcel list on a schedule."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: DhlEcommerceApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.api = api

    async def _async_update_data(self) -> list[dict]:
        try:
            return await self.api.async_get_parcels()
        except DhlAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except DhlApiError as err:
            raise UpdateFailed(str(err)) from err
