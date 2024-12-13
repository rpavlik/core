"""Tests for the RDW config flow."""

from unittest.mock import MagicMock

import pytest
from vehicle.exceptions import RDWConnectionError, RDWUnknownLicensePlateError

from homeassistant.components.rdw.const import CONF_LICENSE_PLATE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.mark.usefixtures("mock_rdw_config_flow", "mock_setup_entry")
async def test_full_user_flow(hass: HomeAssistant) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LICENSE_PLATE: "11-ZKZ-3",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "11-ZKZ-3"
    assert config_entry.data == {CONF_LICENSE_PLATE: "11ZKZ3"}
    assert not config_entry.options


@pytest.mark.usefixtures("mock_setup_entry")
async def test_full_flow_with_authentication_error(
    hass: HomeAssistant, mock_rdw_config_flow: MagicMock
) -> None:
    """Test the full user configuration flow with incorrect license plate.

    This tests tests a full config flow, with a case the user enters an invalid
    license plate, but recover by entering the correct one.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_rdw_config_flow.vehicle.side_effect = RDWUnknownLicensePlateError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LICENSE_PLATE: "0001TJ",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown_license_plate"}

    mock_rdw_config_flow.vehicle.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LICENSE_PLATE: "11-ZKZ-3",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "11-ZKZ-3"
    assert config_entry.data == {CONF_LICENSE_PLATE: "11ZKZ3"}
    assert not config_entry.options


async def test_connection_error(
    hass: HomeAssistant, mock_rdw_config_flow: MagicMock
) -> None:
    """Test API connection error."""
    mock_rdw_config_flow.vehicle.side_effect = RDWConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_LICENSE_PLATE: "0001TJ"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Ensure we can recover from this error
    mock_rdw_config_flow.vehicle.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LICENSE_PLATE: "11-ZKZ-3",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "11-ZKZ-3"
    assert config_entry.data == {CONF_LICENSE_PLATE: "11ZKZ3"}
    assert not config_entry.options
