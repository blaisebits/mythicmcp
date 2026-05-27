"""Callback helpers for integration tests."""

from __future__ import annotations

import asyncio
import time


async def get_callback_for_payload(mythic_instance, payload_uuid: str) -> int | None:
    """Find the callback created for a payload UUID.

    Webshell agents create a placeholder callback via SendMythicRPCCallbackCreate
    at payload generation time. This finds that callback by matching the payload UUID.

    Args:
        mythic_instance: Authenticated Mythic connection.
        payload_uuid: UUID of the generated payload.

    Returns:
        Callback display_id or None if not found.
    """
    from mythic import mythic

    callbacks = await mythic.get_all_callbacks(mythic_instance)
    for cb in callbacks:
        if cb.get("payload", {}).get("uuid") == payload_uuid:
            return cb["display_id"]
    return None


async def get_baseline_callback_ids(mythic_instance) -> set[int]:
    """Capture current active callback IDs before payload execution.

    Returns:
        Set of all current active callback display_ids.
    """
    from mythic import mythic

    callbacks = await mythic.get_all_active_callbacks(mythic_instance)
    return {cb["display_id"] for cb in callbacks}


async def wait_for_callback(
    mythic_instance,
    hostname: str,
    agent_type: str,
    timeout: int = 120,
    poll_interval: int = 5,
    baseline_ids: set[int] | None = None,
) -> int:
    """Poll for a new callback matching expected criteria.

    Args:
        mythic_instance: Authenticated Mythic connection.
        hostname: Expected hostname in callback (case-insensitive match).
        agent_type: Expected agent/payload type name.
        timeout: Maximum wait time in seconds.
        poll_interval: Seconds between polls.
        baseline_ids: Callback IDs to exclude (pre-existing).

    Returns:
        Callback display_id of the new callback.

    Raises:
        TimeoutError: No matching callback within timeout.
    """
    from mythic import mythic

    if baseline_ids is None:
        baseline_ids = set()

    start = time.time()
    hostname_lower = hostname.lower()

    while (time.time() - start) < timeout:
        callbacks = await mythic.get_all_active_callbacks(mythic_instance)
        for cb in callbacks:
            cb_id = cb["display_id"]
            if cb_id in baseline_ids:
                continue

            cb_host = (cb.get("host") or "").lower()
            cb_agent = (cb.get("payload", {}).get("payloadtype", {}).get("name") or "")

            if cb_host == hostname_lower and cb_agent == agent_type:
                return cb_id

        await asyncio.sleep(poll_interval)

    elapsed = int(time.time() - start)
    raise TimeoutError(
        f"No callback found matching hostname='{hostname}', agent_type='{agent_type}' "
        f"after {elapsed}s (timeout={timeout}s). "
        f"Excluded {len(baseline_ids)} baseline callback(s)."
    )
