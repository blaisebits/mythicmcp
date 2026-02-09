"""Payload upload and execution helpers for integration tests."""

from __future__ import annotations

import logging
import ntpath

from tests.integration.config_models import AgentConfig, TargetConfig
from tests.integration.helpers.payload import _stamp_filename

logger = logging.getLogger(__name__)


async def kill_existing_payload_process(
    mythic_instance,
    target: TargetConfig,
) -> None:
    """Kill any running process that matches the payload filename on the target.

    Best-effort: logs a warning on failure instead of raising.
    Must run before upload to avoid "file in use" errors from prior test runs.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target system config (includes upload_path and callback_id).
    """
    from mythic import mythic

    # ntpath handles Windows backslash paths correctly even on Linux
    filename = ntpath.basename(target.upload_path)

    if target.os == "Windows":
        command_str = f"taskkill /F /IM {filename}"
    else:
        command_str = f"pkill -f {filename}"

    try:
        await mythic.issue_task(
            mythic_instance,
            command_name="shell",
            parameters=command_str,
            callback_display_id=target.callback_id,
            wait_for_complete=True,
            timeout=30,
        )
        logger.info("Killed existing process '%s' on %s", filename, target.name)
    except Exception as e:
        # Non-fatal — process may not exist
        logger.info(
            "No existing process '%s' to kill on %s (or kill failed: %s)",
            filename,
            target.name,
            e,
        )


async def upload_payload_to_target(
    mythic_instance,
    payload_bytes: bytes,
    target: TargetConfig,
    agent_config: AgentConfig,
) -> str:
    """Upload a payload to a target system via an existing callback.

    Args:
        mythic_instance: Authenticated Mythic connection.
        payload_bytes: Raw payload content.
        target: Target system configuration.
        agent_config: Agent config (for filename).

    Returns:
        Mythic file_id of the uploaded file.
    """
    from mythic import mythic

    # Register the file with Mythic — returns file_id string directly
    stamped_name = _stamp_filename(agent_config.filename)
    file_id = await mythic.register_file(
        mythic_instance,
        filename=stamped_name,
        contents=payload_bytes,
    )
    if not file_id:
        raise RuntimeError("register_file returned empty file_id")

    # Issue upload task to the pre-existing callback.
    # Apollo's upload command requires "file" (the file_id) and "remote_path".
    # The file_id must appear both in the parameters AND in file_ids.
    result = await mythic.issue_task(
        mythic_instance,
        command_name="upload",
        parameters={"file": file_id, "remote_path": target.upload_path},
        callback_display_id=target.callback_id,
        file_ids=[file_id],
        wait_for_complete=True,
        timeout=120,
    )

    # Check for task-level errors (issue_task may return without raising)
    if isinstance(result, dict) and "error" in result.get("status", "").lower():
        stderr = result.get("stderr", "")
        raise RuntimeError(f"Upload task failed: {result.get('status')}. {stderr}")

    return file_id


async def execute_payload_on_target(
    mythic_instance,
    target: TargetConfig,
    agent_config: AgentConfig,
) -> None:
    """Execute an uploaded payload on the target system.

    Uses the 'run' command which executes directly without cmd.exe wrapper.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target system config (includes upload_path and callback_id).
        agent_config: Agent config (for OS-appropriate execution command).
    """
    from mythic import mythic

    if target.os == "Windows":
        # Use 'run' for direct execution (no cmd.exe wrapper)
        command_str = target.upload_path
    else:
        # Linux: make executable and run in background
        command_str = f"chmod +x {target.upload_path} && {target.upload_path} &"

    await mythic.issue_task(
        mythic_instance,
        command_name="run",
        parameters=command_str,
        callback_display_id=target.callback_id,
        wait_for_complete=False,
        timeout=30,
    )
