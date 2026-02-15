"""Integration tests for payload upload and execution (US3)."""

from __future__ import annotations

import pytest

from tests.integration.config_models import IntegrationTestConfig
from tests.integration.helpers.callback import get_baseline_callback_ids
from tests.integration.helpers.deployment import (
    kill_existing_payload_process,
    upload_payload_to_target,
    execute_payload_on_target,
)
from tests.integration import state


pytestmark = pytest.mark.integration


def _get_agent_config(config: IntegrationTestConfig, agent_name: str):
    for agent in config.agents:
        if agent.name == agent_name:
            return agent
    raise ValueError(f"Agent '{agent_name}' not found")


class TestPayloadDeployment:
    """Test payload upload and execution on target systems."""

    async def test_upload_payload(self, integration_config, mythic_instance):
        """Upload payload to each configured target."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                if not state.check_phase_passed(agent_name, target.name, "download"):
                    pytest.skip(
                        f"Payload download failed for {agent_name}/{target.name}"
                    )

                agent_config = _get_agent_config(integration_config, agent_name)
                s = state.get_state(agent_name, target.name)
                payload_bytes = s.get("payload_bytes")
                assert payload_bytes, f"No payload bytes for {agent_name}/{target.name}"

                try:
                    # Kill any leftover process from a prior run to avoid file locks
                    await kill_existing_payload_process(
                        mythic_instance, target
                    )

                    # Capture baseline callback IDs before upload
                    baseline_ids = await get_baseline_callback_ids(mythic_instance)
                    s["baseline_callback_ids"] = baseline_ids

                    file_id = await upload_payload_to_target(
                        mythic_instance, payload_bytes, target, agent_config
                    )
                    s["file_id"] = file_id
                    state.set_phase_result(agent_name, target.name, "upload", True)

                except Exception as e:
                    state.set_phase_result(agent_name, target.name, "upload", False)
                    pytest.fail(
                        f"Payload upload failed for {agent_name}/{target.name}: {e}"
                    )

    async def test_execute_payload(self, integration_config, mythic_instance):
        """Execute uploaded payload on each configured target."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                if not state.check_phase_passed(agent_name, target.name, "upload"):
                    pytest.skip(
                        f"Payload upload failed for {agent_name}/{target.name}"
                    )

                agent_config = _get_agent_config(integration_config, agent_name)

                try:
                    await execute_payload_on_target(
                        mythic_instance, target, agent_config
                    )
                    state.set_phase_result(agent_name, target.name, "execution", True)

                except Exception as e:
                    state.set_phase_result(agent_name, target.name, "execution", False)
                    pytest.fail(
                        f"Payload execution failed for {agent_name}/{target.name}: {e}"
                    )
