"""Integration tests for callback verification (US4)."""

from __future__ import annotations

import pytest

from tests.integration.config_models import IntegrationTestConfig
from tests.integration.helpers.callback import wait_for_callback
from tests.integration import state


pytestmark = pytest.mark.integration


def _get_agent_config(config: IntegrationTestConfig, agent_name: str):
    for agent in config.agents:
        if agent.name == agent_name:
            return agent
    raise ValueError(f"Agent '{agent_name}' not found")


class TestCallbackVerification:
    """Verify new callbacks appear after payload execution."""

    async def test_verify_callback(self, integration_config, mythic_instance):
        """Poll for new callback matching target hostname and agent type."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                if not state.check_phase_passed(agent_name, target.name, "execution"):
                    pytest.skip(
                        f"Payload execution failed for {agent_name}/{target.name}"
                    )

                agent_config = _get_agent_config(integration_config, agent_name)
                s = state.get_state(agent_name, target.name)

                # Webshell callbacks are already captured in test_03
                if agent_config.is_webshell:
                    new_callback_id = s.get("new_callback_id")
                    assert new_callback_id, (
                        f"Webshell callback not found in state for "
                        f"{agent_name}/{target.name} — test_03 should have set it"
                    )
                    # Already marked callback_verification=True in test_03
                    continue

                baseline_ids = s.get("baseline_callback_ids", set())

                try:
                    new_callback_id = await wait_for_callback(
                        mythic_instance,
                        hostname=target.hostname,
                        agent_type=agent_config.payload_type,
                        timeout=integration_config.timeouts.callback_verification,
                        poll_interval=integration_config.timeouts.polling_interval,
                        baseline_ids=baseline_ids,
                    )
                    assert isinstance(new_callback_id, int) and new_callback_id > 0, (
                        f"Invalid callback ID for {agent_name}/{target.name}: {new_callback_id}"
                    )

                    s["new_callback_id"] = new_callback_id
                    state.set_phase_result(
                        agent_name, target.name, "callback_verification", True
                    )

                except Exception as e:
                    state.set_phase_result(
                        agent_name, target.name, "callback_verification", False
                    )
                    pytest.fail(
                        f"Callback verification failed for {agent_name}/{target.name}: {e}"
                    )
