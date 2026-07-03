"""Sensor platform for DHL eCommerce (NL)."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IN_TRANSIT_CATEGORIES
from .coordinator import DhlDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DHL sensor from a config entry."""
    coordinator: DhlDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DhlParcelsSensor(coordinator, entry)])


class DhlParcelsSensor(CoordinatorEntity[DhlDataUpdateCoordinator], SensorEntity):
    """Number of parcels currently in transit, with details as attributes."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:package-variant-closed"
    _attr_native_unit_of_measurement = "packages"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: DhlDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        # Device name "DHL eCommerce" + entity name "Packages" ->
        # entity_id sensor.dhl_ecommerce_packages.
        self._attr_name = "Packages"
        self._attr_unique_id = f"{entry.entry_id}_parcels"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="DHL eCommerce",
            manufacturer="DHL",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _parcels(self) -> list[dict]:
        return self.coordinator.data or []

    @property
    def _in_transit(self) -> list[dict]:
        return [
            p
            for p in self._parcels
            if p.get("category") in IN_TRANSIT_CATEGORIES
        ]

    @property
    def native_value(self) -> int:
        return len(self._in_transit)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "parcels": self._in_transit,
            "delivered": [
                p for p in self._parcels if p.get("category") == "DELIVERED"
            ],
            "total": len(self._parcels),
        }
