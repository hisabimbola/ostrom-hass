"""Test the Ostrom config flow."""
from unittest.mock import patch

import pytest
from custom_components.ostrom_hass.api import (OstromAuthError,
                                               OstromConnectionError)
from custom_components.ostrom_hass.const import (CONF_CLIENT_ID,
                                                 CONF_CLIENT_SECRET,
                                                 CONF_ZIP_CODE, DOMAIN)
from homeassistant import config_entries, data_entry_flow

TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"
TEST_ZIP_CODE = "12345"


async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "custom_components.ostrom_hass.config_flow.validate_input",
        return_value={"title": f"Ostrom ({TEST_ZIP_CODE})"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: TEST_CLIENT_ID,
                CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
                CONF_ZIP_CODE: TEST_ZIP_CODE,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Ostrom ({TEST_ZIP_CODE})"
    assert result2["data"] == {
        CONF_CLIENT_ID: TEST_CLIENT_ID,
        CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
        CONF_ZIP_CODE: TEST_ZIP_CODE,
    }


async def test_form_invalid_auth(hass):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ostrom_hass.config_flow.validate_input",
        side_effect=OstromAuthError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: TEST_CLIENT_ID,
                CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
                CONF_ZIP_CODE: TEST_ZIP_CODE,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ostrom_hass.config_flow.validate_input",
        side_effect=OstromConnectionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: TEST_CLIENT_ID,
                CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
                CONF_ZIP_CODE: TEST_ZIP_CODE,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
