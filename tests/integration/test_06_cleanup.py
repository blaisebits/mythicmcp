"""Integration tests for cleanup after command execution (Phase 8)."""

from __future__ import annotations

import warnings

import pytest

from tests.integration.config_models import IntegrationTestConfig
from tests.integration.helpers.cleanup import (
    cleanup_payload_on_target,
    deactivate_callback,
)
from tests.integration import state


pytestmark = pytest.mark.integration


class TestCleanup:
    """Remove uploaded payloads and deactivate new callbacks."""

    async def test_cleanup_payload(self, integration_config, mythic_instance):
        """Remove uploaded payload files from target systems."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                # Cleanup is best-effort — don't skip if earlier phases failed,
                # but warn if cleanup itself fails (per FR-020).
                success = await cleanup_payload_on_target(mythic_instance, target)
                if not success:
                    warnings.warn(
                        f"Payload cleanup failed for {agent_name}/{target.name}",
                        stacklevel=1,
                    )

    async def test_deactivate_callback(self, integration_config, mythic_instance):
        """Deactivate callbacks created during testing."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                s = state.get_state(agent_name, target.name)
                new_callback_id = s.get("new_callback_id")

                if not new_callback_id:
                    # No callback was created — nothing to deactivate
                    continue

                success = await deactivate_callback(mythic_instance, new_callback_id)
                if not success:
                    warnings.warn(
                        f"Callback deactivation failed for {agent_name}/{target.name} "
                        f"(callback {new_callback_id})",
                        stacklevel=1,
                    )
