"""Payload generation and download helpers for integration tests."""

from __future__ import annotations

from tests.integration.config_models import AgentConfig


class PayloadBuildError(Exception):
    """Raised when payload build fails on the Mythic server."""


class PayloadDownloadError(Exception):
    """Raised when payload download fails or returns empty content."""


async def generate_payload(
    mythic_instance,
    agent_config: AgentConfig,
    timeout: int = 300,
) -> str:
    """Generate a payload on the Mythic server.

    Args:
        mythic_instance: Authenticated Mythic connection.
        agent_config: Agent configuration from YAML.
        timeout: Build timeout in seconds.

    Returns:
        Payload UUID string.

    Raises:
        PayloadBuildError: Build completed with error status.
    """
    from mythic import mythic

    c2_profiles = [
        {
            "c2_profile": profile.c2_profile,
            "c2_profile_parameters": profile.c2_profile_parameters,
        }
        for profile in agent_config.c2_profiles
    ]

    build_parameters = [
        {"name": param.name, "value": param.value}
        for param in agent_config.build_parameters
    ]

    result = await mythic.create_payload(
        mythic_instance,
        payload_type_name=agent_config.payload_type,
        operating_system=agent_config.os,
        c2_profiles=c2_profiles,
        build_parameters=build_parameters,
        filename=agent_config.filename,
        description=agent_config.description,
        return_on_complete=True,
        timeout=timeout,
    )

    if result.get("build_phase") != "success":
        build_msg = result.get("build_message", "unknown error")
        build_stderr = result.get("build_stderr", "")
        raise PayloadBuildError(
            f"Payload build failed for {agent_config.name}: {build_msg}. "
            f"stderr: {build_stderr}"
        )

    return result["uuid"]


async def download_payload(mythic_instance, payload_uuid: str) -> bytes:
    """Download a built payload from the Mythic server.

    Args:
        mythic_instance: Authenticated Mythic connection.
        payload_uuid: UUID from generate_payload().

    Returns:
        Raw payload bytes.

    Raises:
        PayloadDownloadError: Download failed or returned empty content.
    """
    from mythic import mythic

    result = await mythic.download_payload(mythic_instance, payload_uuid)

    if not result:
        raise PayloadDownloadError(
            f"Payload download returned empty content for UUID {payload_uuid}"
        )

    return result
