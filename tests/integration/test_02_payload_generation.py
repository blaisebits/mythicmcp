"""Integration tests for payload generation and download (US2)."""

from __future__ import annotations

import pytest

from tests.integration.config_models import IntegrationTestConfig
from tests.integration.helpers.payload import generate_payload, download_payload
from tests.integration import state


pytestmark = pytest.mark.integration


def _agent_ids(config: IntegrationTestConfig) -> list[str]:
    """Extract agent names for parametrization."""
    return [agent.name for agent in config.agents]


def _get_agent_config(config: IntegrationTestConfig, agent_name: str):
    """Look up an agent config by name."""
    for agent in config.agents:
        if agent.name == agent_name:
            return agent
    raise ValueError(f"Agent '{agent_name}' not found in config")


class TestPayloadGeneration:
    """Test payload generation for each configured agent."""

    @pytest.fixture(params=None)
    def agent_name(self, request, integration_config):
        """Parametrize by agent name from config."""
        return request.param

    @staticmethod
    def pytest_generate_tests(metafunc):
        """Dynamic parametrization based on config file."""
        # This will be handled via indirect parametrization at collection time
        pass

    async def test_generate_payload(self, integration_config, mythic_instance):
        """Generate a payload for each configured agent."""
        for agent_config in integration_config.agents:
            agent_name = agent_config.name
            try:
                payload_uuid = await generate_payload(
                    mythic_instance,
                    agent_config,
                    timeout=integration_config.timeouts.payload_generation,
                )
                assert payload_uuid, f"Payload UUID is empty for {agent_name}"

                # Store in shared state for all targets that use this agent
                for target in integration_config.targets:
                    if agent_name in target.agents:
                        s = state.get_state(agent_name, target.name)
                        s["payload_uuid"] = payload_uuid
                        state.set_phase_result(agent_name, target.name, "generation", True)

            except Exception as e:
                # Record failure for all targets using this agent
                for target in integration_config.targets:
                    if agent_name in target.agents:
                        state.set_phase_result(agent_name, target.name, "generation", False)
                pytest.fail(f"Payload generation failed for {agent_name}: {e}")

    async def test_download_payload(self, integration_config, mythic_instance):
        """Download the generated payload for each configured agent."""
        for agent_config in integration_config.agents:
            agent_name = agent_config.name

            # Find any target that uses this agent to check phase result
            target_for_agent = None
            for target in integration_config.targets:
                if agent_name in target.agents:
                    target_for_agent = target
                    break

            if target_for_agent is None:
                continue

            if not state.check_phase_passed(agent_name, target_for_agent.name, "generation"):
                pytest.skip(f"Payload generation failed for {agent_name}")

            s = state.get_state(agent_name, target_for_agent.name)
            payload_uuid = s.get("payload_uuid")
            assert payload_uuid, f"No payload UUID found for {agent_name}"

            try:
                payload_bytes = await download_payload(mythic_instance, payload_uuid)
                assert len(payload_bytes) > 0, f"Payload is empty for {agent_name}"

                # Store bytes in state for all targets using this agent
                for target in integration_config.targets:
                    if agent_name in target.agents:
                        s2 = state.get_state(agent_name, target.name)
                        s2["payload_bytes"] = payload_bytes
                        state.set_phase_result(agent_name, target.name, "download", True)

            except Exception as e:
                for target in integration_config.targets:
                    if agent_name in target.agents:
                        state.set_phase_result(agent_name, target.name, "download", False)
                pytest.fail(f"Payload download failed for {agent_name}: {e}")
