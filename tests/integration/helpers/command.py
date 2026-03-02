"""Command execution helpers for integration tests."""

from __future__ import annotations

import base64
import re

from tests.integration.config_models import TestCommandConfig


async def execute_test_command(
    mythic_instance,
    callback_id: int,
    command: TestCommandConfig,
    file_ids: list[str] | None = None,
) -> tuple[bool, str]:
    """Execute a single test command and validate output.

    Args:
        mythic_instance: Authenticated Mythic connection.
        callback_id: Callback display_id to execute on.
        command: Test command configuration.
        file_ids: Optional list of Mythic file UUIDs to attach to the task.

    Returns:
        Tuple of (passed, output). If no expected_output is set, passed is True
        as long as the command completes without error.
    """
    from mythic import mythic

    kwargs: dict = dict(
        command_name=command.command,
        parameters=command.parameters,
        callback_display_id=callback_id,
        wait_for_complete=True,
        timeout=command.timeout,
    )
    if file_ids:
        kwargs["file_ids"] = file_ids

    task = await mythic.issue_task(mythic_instance, **kwargs)

    task_id = task["id"]
    output_parts = await mythic.get_all_task_output_by_id(mythic_instance, task_id)

    # Combine all output parts — responses use base64-encoded response_text
    if isinstance(output_parts, list):
        decoded_parts = []
        for part in output_parts:
            raw = part.get("response_text", "")
            try:
                decoded_parts.append(base64.b64decode(raw).decode("utf-8", errors="replace"))
            except Exception:
                decoded_parts.append(raw)
        output = "".join(decoded_parts)
    else:
        output = str(output_parts)

    if command.expected_output is None:
        return (True, output)

    # Try regex match first; fall back to substring on invalid regex
    try:
        match = re.search(command.expected_output, output)
        return (bool(match), output)
    except re.error:
        return (command.expected_output in output, output)
