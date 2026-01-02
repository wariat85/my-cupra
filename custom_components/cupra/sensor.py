"""Sensor platform for the CUPRA integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import LENGTH_KILOMETERS, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VEHICLE_MODEL, CONF_VEHICLE_NAME, CONF_VIN, DOMAIN, MANUFACTURER
from .coordinator import CupraDataUpdateCoordinator


@dataclass
class CupraSensorEntityDescription(SensorEntityDescription):
    """Descriptor for CUPRA sensors."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None


SENSOR_TYPES: tuple[CupraSensorEntityDescription, ...] = (
    CupraSensorEntityDescription(
        key="battery_level",
        name="Stato batteria",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("batteryLevel"),
        icon="mdi:battery-high",
    ),
    CupraSensorEntityDescription(
        key="range_km",
        name="Autonomia",
        native_unit_of_measurement=LENGTH_KILOMETERS,
        value_fn=lambda data: data.get("remainingRange"),
        icon="mdi:map-marker-distance",
    ),
    CupraSensorEntityDescription(
        key="odometer",
        name="Chilometraggio",
        native_unit_of_measurement=LENGTH_KILOMETERS,
        value_fn=lambda data: data.get("odometer"),
        icon="mdi:counter",
    ),
    CupraSensorEntityDescription(
        key="charging_status",
        name="Stato ricarica",
        value_fn=lambda data: data.get("chargingStatus"),
        icon="mdi:ev-station",
    ),
    CupraSensorEntityDescription(
        key="last_updated",
        name="Ultimo aggiornamento",
        device_class="timestamp",
        value_fn=lambda data: data.get("last_updated"),
        icon="mdi:update",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities
) -> None:
    """Set up CUPRA sensors from a config entry."""
    coordinator: CupraDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    vehicle_model = entry.data.get(CONF_VEHICLE_MODEL, "CUPRA")

    entities: list[CupraSensor] = [
        CupraSensor(coordinator, vin, vehicle_name, vehicle_model, description)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class CupraSensor(CoordinatorEntity[CupraDataUpdateCoordinator], SensorEntity):
    """Representation of a CUPRA vehicle sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CupraDataUpdateCoordinator,
        vin: str,
        vehicle_name: str,
        vehicle_model: str,
        description: CupraSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._vin = vin
        self._attr_unique_id = f"{vin}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer=MANUFACTURER,
            model=vehicle_model,
            name=vehicle_name,
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if self.entity_description.value_fn:
            value = self.entity_description.value_fn(data)
            return value
        return data.get(self.entity_description.key)
