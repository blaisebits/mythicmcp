"""Integration tests for Mythic server connection."""

from __future__ import annotations

import pytest

from mythicmcp.config import load_config
from mythicmcp.connection import connect_to_mythic, MythicContext


pytestmark = pytest.mark.integration


class TestMythicConnection:
    """Test real Mythic server connection."""

    async def test_connect_with_api_token(self):
        """Test connecting to Mythic with API token."""
        config = load_config()

        mythic_instance = await connect_to_mythic(config)

        assert mythic_instance is not None

    async def test_mythic_instance_authenticated(self):
        """Test that connected instance is authenticated."""
        config = load_config()

        mythic_instance = await connect_to_mythic(config)

        # When using API token, apitoken is set; when using credentials, access_token is set
        if config.uses_api_token:
            assert mythic_instance.apitoken is not None
        else:
            assert mythic_instance.access_token is not None

    async def test_can_check_current_operation(self):
        """Test that we can check the current operation status."""
        config = load_config()

        mythic_instance = await connect_to_mythic(config)

        # current_operation_id may be 0/None if no operation is set
        # but the attribute should exist
        assert hasattr(mythic_instance, 'current_operation_id')
