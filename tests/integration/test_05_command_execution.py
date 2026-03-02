"""Integration tests for test command execution (US5)."""

from __future__ import annotations

import copy

import pytest

from tests.integration.config_models import IntegrationTestConfig
from tests.integration.helpers.command import execute_test_command
from tests.integration import state


pytestmark = pytest.mark.integration

_PLACEHOLDER = "REPLACE_WITH_FILE_ID"


def _substitute_file_id(parameters, file_id: str):
    """Replace REPLACE_WITH_FILE_ID in command parameters with actual file_id."""
    if isinstance(parameters, str):
        return parameters.replace(_PLACEHOLDER, file_id)
    if isinstance(parameters, dict):
        out = {}
        for k, v in parameters.items():
            if isinstance(v, str) and _PLACEHOLDER in v:
                out[k] = v.replace(_PLACEHOLDER, file_id)
            else:
                out[k] = v
        return out
    return parameters


class TestCommandExecution:
    """Execute configured test commands on verified callbacks."""

    async def test_run_commands(
        self, integration_config, mythic_instance, test_file_id
    ):
        """Run each configured command on verified callbacks."""
        for target in integration_config.targets:
            for agent_name in target.agents:
                if not state.check_phase_passed(
                    agent_name, target.name, "callback_verification"
                ):
                    pytest.skip(
                        f"Callback verification failed for {agent_name}/{target.name}"
                    )

                s = state.get_state(agent_name, target.name)
                new_callback_id = s.get("new_callback_id")
                assert new_callback_id, (
                    f"No callback ID for {agent_name}/{target.name}"
                )

                commands = integration_config.test_commands.get(agent_name, [])
                for cmd in commands:
                    # Substitute file_id placeholder in parameters
                    resolved_cmd = copy.deepcopy(cmd)
                    resolved_cmd.parameters = _substitute_file_id(
                        resolved_cmd.parameters, test_file_id
                    )

                    try:
                        passed, output = await execute_test_command(
                            mythic_instance, new_callback_id, resolved_cmd
                        )

                        if resolved_cmd.expected_output is not None:
                            assert passed, (
                                f"Command '{cmd.command}' on {agent_name}/{target.name} "
                                f"expected output matching '{cmd.expected_output}', "
                                f"got: {output!r}"
                            )

                    except Exception as e:
                        state.set_phase_result(
                            agent_name, target.name, "command_execution", False
                        )
                        pytest.fail(
                            f"Command '{cmd.command}' failed on "
                            f"{agent_name}/{target.name}: {e}"
                        )

                state.set_phase_result(
                    agent_name, target.name, "command_execution", True
                )
