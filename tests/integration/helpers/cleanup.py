"""Cleanup helpers for integration tests."""

from __future__ import annotations

import logging

from tests.integration.config_models import TargetConfig

logger = logging.getLogger(__name__)


async def cleanup_payload_on_target(
    mythic_instance,
    target: TargetConfig,
    agent_type: str = "apollo",
) -> bool:
    """Remove the uploaded payload file from the target system.

    Best-effort: logs warning on failure instead of raising.

    Args:
        mythic_instance: Authenticated Mythic connection.
        target: Target config (includes upload_path and callback_id).
        agent_type: Agent payload type (determines shell vs run command).

    Returns:
        True if cleanup succeeded, False otherwise.
    """
    from mythic import mythic

    if target.os == "Windows":
        command_str = f"del {target.upload_path}"
    else:
        command_str = f"rm -f {target.upload_path}"

    # Only Apollo has 'run'; other agents use 'shell'
    agents_with_run = {"apollo"}
    command_name = "run" if agent_type in agents_with_run else "shell"

    try:
        await mythic.issue_task(
            mythic_instance,
            command_name=command_name,
            parameters=command_str,
            callback_display_id=target.callback_id,
            wait_for_complete=True,
            timeout=30,
        )
        return True
    except Exception as e:
        logger.warning(
            "Failed to clean up payload on %s (callback %d): %s",
            target.name,
            target.callback_id,
            e,
        )
        return False


async def deactivate_callback(
    mythic_instance,
    callback_display_id: int,
) -> bool:
    """Deactivate a callback created during testing.

    Best-effort: logs warning on failure instead of raising.

    Args:
        mythic_instance: Authenticated Mythic connection.
        callback_display_id: Callback to deactivate.

    Returns:
        True if deactivation succeeded, False otherwise.
    """
    from mythic import mythic

    try:
        await mythic.update_callback(
            mythic_instance,
            callback_display_id,
            active=False,
        )
        return True
    except Exception as e:
        logger.warning(
            "Failed to deactivate callback %d: %s",
            callback_display_id,
            e,
        )
        return False
