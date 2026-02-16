"""Integration tests for test command execution (US5)."""

from __future__ import annotations

import copy
import logging
from pathlib import Path

import pytest

from tests.integration.config_models import IntegrationTestConfig, TestCommandConfig
from tests.integration.helpers.command import execute_test_command
from tests.integration import state


pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

FIXTURE_FILE = Path(__file__).parent / "fixtures" / "test_upload.txt"
FILE_ID_PLACEHOLDER = "REPLACE_WITH_FILE_ID"


async def _upload_test_fixture(mythic_instance) -> str:
    """Upload the test fixture file to Mythic and return its file_id."""
    from mythic import mythic

    content = FIXTURE_FILE.read_bytes()
    file_id = await mythic.register_file(
        mythic_instance,
        filename=FIXTURE_FILE.name,
        contents=content,
    )
    if not file_id:
        raise RuntimeError("register_file returned empty file_id")
    logger.info("Uploaded test fixture as file_id=%s", file_id)
    return file_id


def _substitute_file_id(
    commands: list[TestCommandConfig], file_id: str
) -> list[TestCommandConfig]:
    """Deep-copy commands and replace REPLACE_WITH_FILE_ID with actual file_id."""
    patched: list[TestCommandConfig] = []
    for cmd in commands:
        params = cmd.parameters
        needs_patch = False
        if isinstance(params, dict):
            for v in params.values():
                if v == FILE_ID_PLACEHOLDER:
                    needs_patch = True
                    break
        elif isinstance(params, str) and FILE_ID_PLACEHOLDER in params:
            needs_patch = True

        if needs_patch:
            params = copy.deepcopy(params)
            if isinstance(params, dict):
                params = {
                    k: (file_id if v == FILE_ID_PLACEHOLDER else v)
                    for k, v in params.items()
                }
            else:
                params = params.replace(FILE_ID_PLACEHOLDER, file_id)
            patched.append(cmd.model_copy(update={"parameters": params}))
        else:
            patched.append(cmd)
    return patched


class TestCommandExecution:
    """Execute configured test commands on verified callbacks."""

    async def test_run_commands(self, integration_config, mythic_instance):
        """Run each configured command on verified callbacks."""
        # Upload test fixture once for file-op tests
        file_id: str | None = None

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

                # Upload fixture and substitute file_id if any command uses placeholder
                has_placeholder = any(
                    (isinstance(c.parameters, dict) and FILE_ID_PLACEHOLDER in c.parameters.values())
                    or (isinstance(c.parameters, str) and FILE_ID_PLACEHOLDER in c.parameters)
                    for c in commands
                )
                if has_placeholder:
                    if file_id is None:
                        file_id = await _upload_test_fixture(mythic_instance)
                    commands = _substitute_file_id(commands, file_id)

                for cmd in commands:
                    # Pass file_ids for upload commands that reference a file_id
                    cmd_file_ids = None
                    if (
                        cmd.command == "upload"
                        and isinstance(cmd.parameters, dict)
                        and file_id
                        and cmd.parameters.get("file") == file_id
                    ):
                        cmd_file_ids = [file_id]

                    try:
                        passed, output = await execute_test_command(
                            mythic_instance,
                            new_callback_id,
                            cmd,
                            file_ids=cmd_file_ids,
                        )

                        if cmd.expected_output is not None:
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
