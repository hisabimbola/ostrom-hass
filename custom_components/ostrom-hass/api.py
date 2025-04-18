"""API client for Ostrom."""
import base64
import logging
from typing import Any, Dict

import aiohttp

from .const import AUTH_URL

_LOGGER = logging.getLogger(__name__)

class OstromApiError(Exception):
    """Base exception for Ostrom API errors."""

class OstromAuthError(OstromApiError):
    """Authentication error."""

class OstromConnectionError(OstromApiError):
    """Connection error."""


class OstromApiClient:
    """API client for Ostrom."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self._session = session or aiohttp.ClientSession()
        self._close_session = session is None  # Close session if we created it

    async def get_access_token(self) -> Dict[str, Any]:
        """Get an access token from Ostrom API.

        Returns:
            Dict with keys: access_token, token_type, expires_in

        Raises:
            OstromAuthError: If authentication fails
            OstromConnectionError: If connection fails
        """
        try:
            # Create base64 encoded auth string
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_str.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {base64_auth}",
            }
            data = {
                "grant_type": "client_credentials",
            }

            async with self._session.post(AUTH_URL, headers=headers, data=data) as response:
                if response.status != 201:
                    _LOGGER.error("Authentication failed with status %s", response.status)
                    raise OstromAuthError("Authentication failed")

                token_data = await response.json()

                # Verify the exact token response format
                required_fields = {"access_token", "token_type", "expires_in"}
                if not all(field in token_data for field in required_fields):
                    _LOGGER.error(
                        "Invalid token response. Missing required fields. Got: %s",
                        ", ".join(token_data.keys())
                    )
                    raise OstromAuthError("Invalid token response format")

                if token_data["token_type"] != "Bearer":
                    _LOGGER.error(
                        "Invalid token type. Expected 'Bearer', got: %s",
                        token_data["token_type"]
                    )
                    raise OstromAuthError("Invalid token type")

                return token_data

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to connect to Ostrom API: %s", err)
            raise OstromConnectionError("Connection failed") from err
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.error("Invalid response format: %s", err)
            raise OstromAuthError("Invalid response format") from err

    async def close(self) -> None:
        """Close the API client."""
        if self._close_session and self._session:
            await self._session.close()
