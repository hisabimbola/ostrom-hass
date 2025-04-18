"""Tests for Ostrom coordinator."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.ostrom_hass.api import (OstromAuthError,
                                               OstromConnectionError)
from custom_components.ostrom_hass.coordinator import OstromDataCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"
TEST_ZIP_CODE = "12345"


@pytest.fixture
def mock_hass():
    """Create a mock hass instance."""
    return AsyncMock()


@pytest.fixture
def coordinator(mock_hass):
    """Create a coordinator instance."""
    return OstromDataCoordinator(
        mock_hass,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_ZIP_CODE,
    )


@pytest.fixture
def mock_api():
    """Create a mock API client."""
    with patch("custom_components.ostrom_hass.coordinator.OstromApiClient") as mock:
        yield mock.return_value


async def test_coordinator_update_success(coordinator, mock_api):
    """Test successful data update."""
    # Mock token response
    mock_api.get_access_token.return_value = {
        "access_token": "test_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    # Mock price data response
    now = datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    next_hour = current_hour + timedelta(hours=1)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "data": [
            {
                "date": current_hour.strftime("%Y-%m-%dT%H:00:00.000Z"),
                "grossKwhPrice": 0.30,
                "grossMonthlyOstromBaseFee": 5.0,
                "grossMonthlyGridFees": 4.0,
            },
            {
                "date": next_hour.strftime("%Y-%m-%dT%H:00:00.000Z"),
                "grossKwhPrice": 0.35,
                "grossMonthlyOstromBaseFee": 5.0,
                "grossMonthlyGridFees": 4.0,
            },
        ]
    }
    mock_api._session.get.return_value.__aenter__.return_value = mock_response

    data = await coordinator._async_update_data()

    assert data["electricity_current_price"] == 0.30
    assert data["electricity_next_hour_price"] == 0.35
    assert data["electricity_lowest_price_today"] == 0.30
    assert data["electricity_highest_price_today"] == 0.35
    assert data["electricity_base_fee"] == 5.0
    assert data["electricity_grid_fee"] == 4.0


async def test_coordinator_auth_error(coordinator, mock_api):
    """Test authentication error handling."""
    mock_api.get_access_token.side_effect = OstromAuthError("Auth failed")

    with pytest.raises(UpdateFailed, match="Auth failed"):
        await coordinator._async_update_data()


async def test_coordinator_connection_error(coordinator, mock_api):
    """Test connection error handling."""
    mock_api.get_access_token.side_effect = OstromConnectionError("Connection failed")

    with pytest.raises(UpdateFailed, match="Connection failed"):
        await coordinator._async_update_data()


async def test_coordinator_no_current_price(coordinator, mock_api):
    """Test handling of missing current price."""
    # Mock token response
    mock_api.get_access_token.return_value = {
        "access_token": "test_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    # Mock empty price data
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": []}
    mock_api._session.get.return_value.__aenter__.return_value = mock_response

    with pytest.raises(UpdateFailed, match="No valid price data found"):
        await coordinator._async_update_data()


async def test_coordinator_cleanup(coordinator, mock_api):
    """Test coordinator cleanup."""
    await coordinator.async_close()
    mock_api.close.assert_called_once()
