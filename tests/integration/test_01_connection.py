"""Integration tests for Mythic server connection via YAML config."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


class TestMythicConnectionFromConfig:
    """Test connecting to Mythic using the integration YAML config."""

    async def test_mythic_connection_from_config(self, mythic_instance):
        """Verify that the Mythic connection succeeds using YAML config credentials."""
        assert mythic_instance is not None

    async def test_mythic_instance_has_operation(self, mythic_instance):
        """Verify that the connected instance has an operation set."""
        assert hasattr(mythic_instance, "current_operation_id")
