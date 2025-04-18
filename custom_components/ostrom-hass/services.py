"""Services for the Ostrom integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import OstromDataCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_GET_PRICES = "get_prices_for_date"

SERVICE_SCHEMA_GET_PRICES = vol.Schema(
    {
        vol.Required("date"): cv.date,
        vol.Optional("zip_code"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Ostrom services."""

    async def get_prices_for_date(call: ServiceCall) -> dict[str, Any]:
        """Get prices for a specific date."""
        date = call.data["date"]
        zip_code = call.data.get("zip_code")

        # Get the coordinator for the specified zip code or first available
        if zip_code and DOMAIN in hass.data:
            coordinator = next(
                (
                    coord
                    for entry_id, coord in hass.data[DOMAIN].items()
                    if isinstance(coord, OstromDataCoordinator)
                    and coord.zip_code == zip_code
                ),
                None,
            )
        else:
            coordinator = next(
                (
                    coord
                    for entry_id, coord in hass.data[DOMAIN].items()
                    if isinstance(coord, OstromDataCoordinator)
                ),
                None,
            )

        if not coordinator:
            raise ValueError(
                f"No Ostrom integration found{f' for ZIP code {zip_code}' if zip_code else ''}"
            )

        # Ensure we have fresh data
        await coordinator.async_refresh()

        if not coordinator.data:
            raise ValueError("No price data available")

        # Filter prices for the requested date
        prices = coordinator.data.get("electricity_prices_today", [])
        date_prices = [
            price
            for price in prices
            if datetime.fromisoformat(price["datetime"]).date() == date
        ]

        if not date_prices:
            raise ValueError(f"No prices found for date {date}")

        return {"prices": date_prices}

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PRICES,
        get_prices_for_date,
        schema=SERVICE_SCHEMA_GET_PRICES,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Ostrom services."""
    if DOMAIN in hass.services.async_services():
        hass.services.async_remove(DOMAIN, SERVICE_GET_PRICES)
