"""Platform for sensor integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import OstromDataCoordinator


@dataclass
class OstromSensorEntityDescription(SensorEntityDescription):
    """Class describing Ostrom sensor entities."""

    key: str  # Required by SensorEntityDescription
    name: str | None = None
    native_unit_of_measurement: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    entity_category: str | None = None
    icon: str | None = None
    value_fn: Callable[[dict[str, Any]], StateType] | None = None


PRICE_SENSORS: tuple[OstromSensorEntityDescription, ...] = (
    OstromSensorEntityDescription(
        key="current_price",
        name="Current Price",
        native_unit_of_measurement=f"{CURRENCY_EURO}/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=None,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_current_price"],
    ),
    OstromSensorEntityDescription(
        key="next_hour_price",
        name="Next Hour Price",
        native_unit_of_measurement=f"{CURRENCY_EURO}/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=None,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_next_hour_price"],
    ),
    OstromSensorEntityDescription(
        key="lowest_price_today",
        name="Lowest Price Today",
        native_unit_of_measurement=f"{CURRENCY_EURO}/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=None,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_lowest_price_today"],
    ),
    OstromSensorEntityDescription(
        key="highest_price_today",
        name="Highest Price Today",
        native_unit_of_measurement=f"{CURRENCY_EURO}/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=None,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_highest_price_today"],
    ),
)

FEE_SENSORS: tuple[OstromSensorEntityDescription, ...] = (
    OstromSensorEntityDescription(
        key="base_fee",
        name="Monthly Base Fee",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_base_fee"],
    ),
    OstromSensorEntityDescription(
        key="grid_fee",
        name="Monthly Grid Fee",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:currency-eur",
        value_fn=lambda data: data["electricity_grid_fee"],
    ),
)

FORECAST_SENSORS: tuple[OstromSensorEntityDescription, ...] = (
    OstromSensorEntityDescription(
        key="prices_today",
        name="Today's Prices",
        icon="mdi:chart-line",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None,  # Value is stored in attributes
    ),
    OstromSensorEntityDescription(
        key="prices_tomorrow",
        name="Tomorrow's Prices",
        icon="mdi:chart-line",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None,  # Value is stored in attributes
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ostrom sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[OstromSensor] = []

    # Add all sensor types
    for description in [*PRICE_SENSORS, *FEE_SENSORS, *FORECAST_SENSORS]:
        entities.append(OstromSensor(coordinator, description))

    async_add_entities(entities, True)


class OstromSensor(CoordinatorEntity[OstromDataCoordinator], SensorEntity):
    """Representation of an Ostrom sensor."""

    entity_description: OstromSensorEntityDescription

    def __init__(
        self,
        coordinator: OstromDataCoordinator,
        description: OstromSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Create the entity ID with the correct format
        self._attr_unique_id = f"{DOMAIN}_{coordinator.zip_code}_{description.key}"
        self.entity_id = f"sensor.{DOMAIN}_{description.key}"

        self._attr_device_info = coordinator.device_info

        # Only set last_reset for TOTAL state class sensors
        if description.state_class == SensorStateClass.TOTAL:
            self._attr_last_reset = dt_util.start_of_local_day()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        if self.entity_description.value_fn is None:
            return None

        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.key == "prices_today":
            return {
                "prices": self.coordinator.data.get("electricity_prices_today", [])
            }
        elif self.entity_description.key == "prices_tomorrow":
            return {
                "prices": self.coordinator.data.get("electricity_prices_tomorrow", [])
            }
        return None
