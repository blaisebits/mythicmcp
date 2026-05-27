"""Payload upload and execution helpers for integration tests."""

from __future__ import annotations

import logging
import ntpath

from tests.integration.config_models import AgentConfig, TargetConfig
from tests.integration.helpers.payload import _stamp_filename

logger = logging.getLogger(__name__)


def _format_shell_params(agent_name: str, command_str: str):
    """Format shell parameters for the given agent.

    All agents (Apollo, Arachne, Poseidon) take a raw command-line string.
    """
    return command_str


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

    # Poseidon shell expects {"command": "..."}, Apollo/Arachne take a raw string
    agent_name = target.agents[0] if target.agents else ""
    shell_params = _format_shell_params(agent_name, command_str)

    try:
        await mythic.issue_task(
            mythic_instance,
            command_name="shell",
            parameters=shell_params,
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


async def delete_existing_payload_file(
    mythic_instance,
    target: TargetConfig,
) -> None:
    """Delete any existing payload file on disk before uploading a new one.

    Best-effort: logs a warning on failure instead of raising.
    Must run after kill_existing_payload_process to avoid "file in use" errors.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target system config (includes upload_path and callback_id).
    """
    from mythic import mythic

    if target.os == "Windows":
        command_str = f"del /F {target.upload_path}"
    else:
        command_str = f"rm -f {target.upload_path}"

    agent_name = target.agents[0] if target.agents else ""
    shell_params = _format_shell_params(agent_name, command_str)

    try:
        await mythic.issue_task(
            mythic_instance,
            command_name="shell",
            parameters=shell_params,
            callback_display_id=target.callback_id,
            wait_for_complete=True,
            timeout=30,
        )
        logger.info("Deleted existing payload file '%s' on %s", target.upload_path, target.name)
    except Exception as e:
        logger.info(
            "No existing payload file '%s' to delete on %s (or delete failed: %s)",
            target.upload_path,
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
    # Apollo uses "file" param, Poseidon uses "file_id" — both need remote_path.
    # The file_id must appear both in the parameters AND in file_ids.
    if agent_config.name == "poseidon":
        upload_params = {
            "file_id": file_id,
            "remote_path": target.upload_path,
            "overwrite": True,
        }
    else:
        upload_params = {"file": file_id, "remote_path": target.upload_path}

    result = await mythic.issue_task(
        mythic_instance,
        command_name="upload",
        parameters=upload_params,
        callback_display_id=target.callback_id,
        file_ids=[file_id],
        wait_for_complete=True,
        timeout=120,
    )

    # Check for task-level errors (issue_task may return without raising)
    if isinstance(result, dict) and "error" in result.get("status", "").lower():
        raise RuntimeError(f"Upload task failed: {result}")

    return file_id


async def execute_payload_on_target(
    mythic_instance,
    target: TargetConfig,
    agent_config: AgentConfig,
) -> None:
    """Execute an uploaded payload on the target system.

    Webshell agents skip execution — the payload is a file served by a web
    server, not a binary to run. Use activate_webshell_callback() instead.

    Uses 'run' for agents that support it (e.g. Apollo), falls back to 'shell'.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target system config (includes upload_path and callback_id).
        agent_config: Agent config (for OS-appropriate execution command).
    """
    from mythic import mythic

    if agent_config.is_webshell:
        logger.info(
            "Skipping execute for webshell agent '%s' on %s",
            agent_config.name, target.name,
        )
        return

    if agent_config.name == "poseidon":
        # Poseidon: chmod+execute via shell (raw string, not dict)
        shell_cmd = f"chmod +x {target.upload_path} && nohup {target.upload_path} &"
        await mythic.issue_task(
            mythic_instance,
            command_name="shell",
            parameters=shell_cmd,
            callback_display_id=target.callback_id,
            wait_for_complete=False,
            timeout=30,
        )
    elif target.os == "Windows":
        # Use 'run' for direct execution (no cmd.exe wrapper)
        await mythic.issue_task(
            mythic_instance,
            command_name="run",
            parameters=target.upload_path,
            callback_display_id=target.callback_id,
            wait_for_complete=False,
            timeout=30,
        )
    else:
        # Linux (non-Poseidon): make executable and run in background
        command_str = f"chmod +x {target.upload_path} && {target.upload_path} &"
        await mythic.issue_task(
            mythic_instance,
            command_name="shell",
            parameters=command_str,
            callback_display_id=target.callback_id,
            wait_for_complete=False,
            timeout=30,
        )


async def activate_webshell_callback(
    mythic_instance,
    payload_uuid: str,
    timeout: int = 60,
    poll_interval: int = 5,
) -> int:
    """Find the placeholder callback for a webshell payload and issue checkin.

    Webshell agents create a placeholder callback at payload generation time
    via SendMythicRPCCallbackCreate. This function locates that callback and
    issues a 'checkin' command to populate host info (IP, OS, user, hostname).

    Must be called AFTER the webshell file is uploaded and reachable at the
    C2 profile URL — checkin will fail if the webshell isn't deployed yet.

    Args:
        mythic_instance: Authenticated Mythic connection.
        payload_uuid: UUID of the generated webshell payload.
        timeout: Max seconds to wait for placeholder callback to appear.
        poll_interval: Seconds between polls.

    Returns:
        Callback display_id of the activated callback.

    Raises:
        TimeoutError: Placeholder callback not found within timeout.
        RuntimeError: Checkin command failed.
    """
    import asyncio
    import time

    from mythic import mythic

    from tests.integration.helpers.callback import get_callback_for_payload

    start = time.time()
    callback_id = None

    while (time.time() - start) < timeout:
        callback_id = await get_callback_for_payload(mythic_instance, payload_uuid)
        if callback_id is not None:
            break
        await asyncio.sleep(poll_interval)

    if callback_id is None:
        raise TimeoutError(
            f"No placeholder callback found for payload {payload_uuid} "
            f"after {int(time.time() - start)}s"
        )

    logger.info("Found placeholder callback %d for payload %s", callback_id, payload_uuid)

    # Issue checkin to populate host info (IP, OS, user, hostname, PID, arch)
    try:
        await mythic.issue_task(
            mythic_instance,
            command_name="checkin",
            parameters="",
            callback_display_id=callback_id,
            wait_for_complete=True,
            timeout=60,
        )
        logger.info("Checkin succeeded on callback %d", callback_id)
    except Exception as e:
        raise RuntimeError(
            f"Checkin failed on callback {callback_id}: {e}"
        ) from e

    return callback_id
