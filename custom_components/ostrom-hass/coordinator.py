"""Data coordinator for the Ostrom integration."""
import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import OstromApiClient, OstromAuthError, OstromConnectionError
from .const import ATTRIBUTION, BASE_URL, DOMAIN, MANUFACTURER, MODEL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OstromDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Ostrom API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        zip_code: str,
    ) -> None:
        """Initialize the data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.zip_code = zip_code
        self.api = OstromApiClient(client_id, client_secret)
        self._access_token = None
        self._token_expires_at = None

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{DOMAIN}_{zip_code}")},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=f"Ostrom Energy ({zip_code})",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self._attr_device_info

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token."""
        if (
            self._access_token is None
            or self._token_expires_at is None
            or datetime.now(timezone.utc) >= self._token_expires_at
        ):
            try:
                token_data = await self.api.get_access_token()
                self._access_token = token_data["access_token"]
                # Set token expiry slightly before actual expiry
                expires_in = int(token_data["expires_in"]) - 60
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                _LOGGER.debug(
                    "Successfully obtained new access token, expires in %d seconds",
                    expires_in
                )
            except (OstromAuthError, OstromConnectionError) as err:
                raise UpdateFailed(str(err))

    async def _fetch_prices(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Fetch prices for a specific date range."""
        try:
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "accept": "application/json",
            }

            url = f"{BASE_URL}/spot-prices"
            params = {
                "startDate": start_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:00:00.000Z"),
                "endDate": end_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:00:00.000Z"),
                "resolution": "HOUR",
                "zip": self.zip_code,
            }

            _LOGGER.debug("Fetching prices with params: %s", params)

            async with async_timeout.timeout(10):
                async with self.api._session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data.get("data"):
                        raise UpdateFailed("No price data received from Ostrom API")

                    _LOGGER.debug("Received %d prices from API", len(data["data"]))
                    return data["data"]

        except Exception as err:
            _LOGGER.error("Error fetching prices: %s", err)
            raise

    def _process_prices(self, prices: list[dict[str, Any]], target_date: datetime) -> list[dict[str, Any]]:
        """Process prices for a specific date."""
        processed_prices = []
        target_date_local = target_date.astimezone(dt_util.DEFAULT_TIME_ZONE)

        for price in prices:
            try:
                # Parse the UTC date from API and convert to local time
                price_date = datetime.fromisoformat(price["date"].replace("Z", "+00:00"))
                price_date_local = price_date.astimezone(dt_util.DEFAULT_TIME_ZONE)

                _LOGGER.debug(
                    "Comparing dates - Price date: %s, Target date: %s",
                    price_date_local.date(),
                    target_date_local.date()
                )

                if price_date_local.date() == target_date_local.date():
                    processed_prices.append({
                        "datetime": price_date_local.isoformat(),
                        "price": price["grossKwhPrice"],
                        "net_price": price["netKwhPrice"],
                        "net_mwh_price": price["netMwhPrice"],
                        "net_tax_and_levies": price["netKwhTaxAndLevies"],
                        "gross_tax_and_levies": price["grossKwhTaxAndLevies"]
                    })
            except (KeyError, ValueError) as err:
                _LOGGER.warning("Error parsing price data: %s", err)
                continue

        return sorted(processed_prices, key=lambda x: x["datetime"])

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Ostrom API."""
        try:
            await self._ensure_token()

            now = dt_util.now()
            tomorrow = now + timedelta(days=1)

            # Fetch today's prices (from yesterday to tomorrow to ensure we have all data)
            today_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

            _LOGGER.debug("Fetching today's prices from %s to %s", today_start, today_end)
            today_prices_raw = await self._fetch_prices(today_start, today_end)

            # Fetch tomorrow's prices (from today to day after tomorrow)
            tomorrow_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = (now + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)

            _LOGGER.debug("Fetching tomorrow's prices from %s to %s", tomorrow_start, tomorrow_end)
            tomorrow_prices_raw = await self._fetch_prices(tomorrow_start, tomorrow_end)

            # Process prices for today and tomorrow
            today_prices = self._process_prices(today_prices_raw, now)
            tomorrow_prices = self._process_prices(tomorrow_prices_raw, tomorrow)

            _LOGGER.debug("Processed %d prices for today", len(today_prices))
            _LOGGER.debug("Processed %d prices for tomorrow", len(tomorrow_prices))

            if not today_prices:
                raise UpdateFailed("No valid price data found for today")

            # Find current and next hour prices
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            next_hour = current_hour + timedelta(hours=1)

            # Convert to local timezone for comparison
            current_hour_local = current_hour.astimezone(dt_util.DEFAULT_TIME_ZONE)
            next_hour_local = next_hour.astimezone(dt_util.DEFAULT_TIME_ZONE)

            _LOGGER.debug("Looking for current hour price at %s", current_hour_local)

            current_price = next(
                (p for p in today_prices
                 if datetime.fromisoformat(p["datetime"]).replace(tzinfo=None) ==
                    current_hour_local.replace(tzinfo=None)),
                None,
            )

            next_price = next(
                (p for p in today_prices + tomorrow_prices
                 if datetime.fromisoformat(p["datetime"]).replace(tzinfo=None) ==
                    next_hour_local.replace(tzinfo=None)),
                None,
            )

            if not current_price:
                _LOGGER.error("Available price times for today: %s",
                            [datetime.fromisoformat(p["datetime"]) for p in today_prices])
                raise UpdateFailed(f"Could not find current hour price for {current_hour_local}")

            # Calculate min/max prices for today
            today_price_values = [p["price"] for p in today_prices]

            return {
                "electricity_current_price": current_price["price"],
                "electricity_gross_current_price": current_price["gross_price"],
                "electricity_next_hour_price": next_price["price"] if next_price else None,
                "electricity_lowest_price_today": min(today_price_values),
                "electricity_highest_price_today": max(today_price_values),
                "electricity_base_fee": float(today_prices_raw[0]["grossMonthlyOstromBaseFee"]),
                "electricity_grid_fee": float(today_prices_raw[0]["grossMonthlyGridFees"]),
                "electricity_prices_today": today_prices,
                "electricity_prices_tomorrow": tomorrow_prices,
                "attribution": ATTRIBUTION,
            }

        except OstromAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}")
        except OstromConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}")
        except asyncio.TimeoutError:
            raise UpdateFailed("Timeout while fetching data from Ostrom API")
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}")

    async def async_close(self) -> None:
        """Close the coordinator."""
        try:
            if hasattr(self.api, '_session') and self.api._session:
                await self.api._session.close()
        except Exception as err:
            _LOGGER.error("Error closing API session: %s", err)
