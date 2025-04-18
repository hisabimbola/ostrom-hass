"""Tests for Ostrom API client."""
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from custom_components.ostrom_hass.api import (OstromApiClient,
                                               OstromAuthError,
                                               OstromConnectionError)

TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.fixture
def api_client(mock_session):
    """Create an API client with a mock session."""
    return OstromApiClient(TEST_CLIENT_ID, TEST_CLIENT_SECRET, session=mock_session)


async def test_get_access_token_success(api_client, mock_session):
    """Test successful token retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "access_token": "test_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    mock_session.post.return_value.__aenter__.return_value = mock_response

    token_data = await api_client.get_access_token()

    assert token_data["access_token"] == "test_token"
    assert token_data["token_type"] == "Bearer"
    assert token_data["expires_in"] == 3600


async def test_get_access_token_auth_error(api_client, mock_session):
    """Test authentication error handling."""
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_session.post.return_value.__aenter__.return_value = mock_response

    with pytest.raises(OstromAuthError):
        await api_client.get_access_token()


async def test_get_access_token_invalid_response(api_client, mock_session):
    """Test invalid response handling."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "invalid": "response"
    }
    mock_session.post.return_value.__aenter__.return_value = mock_response

    with pytest.raises(OstromAuthError):
        await api_client.get_access_token()


async def test_get_access_token_connection_error(api_client, mock_session):
    """Test connection error handling."""
    mock_session.post.side_effect = aiohttp.ClientError()

    with pytest.raises(OstromConnectionError):
        await api_client.get_access_token()


async def test_close_session(mock_session):
    """Test session cleanup."""
    api_client = OstromApiClient(TEST_CLIENT_ID, TEST_CLIENT_SECRET)
    await api_client.close()

    # Session should be closed if created by the client
    assert api_client._close_session is True
