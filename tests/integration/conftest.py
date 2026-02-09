"""Integration test fixtures for MythicMCP.

Provides session-scoped fixtures for config loading and Mythic connection.
"""

from __future__ import annotations

import pytest

from tests.integration.config_models import IntegrationTestConfig, load_integration_config


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def integration_config() -> IntegrationTestConfig:
    """Load the integration test configuration from YAML.

    Skips all tests if config file is not found.
    """
    try:
        return load_integration_config()
    except FileNotFoundError:
        pytest.skip("Integration config not found")


@pytest.fixture(scope="session")
async def mythic_instance(integration_config: IntegrationTestConfig):
    """Connect to Mythic server using config credentials.

    Skips all tests if the Mythic server is unreachable.
    """
    from mythic import mythic

    config = integration_config.mythic

    try:
        if config.api_token:
            instance = await mythic.login(
                server_ip=config.server_url,
                apitoken=config.api_token,
                timeout=config.timeout,
            )
        else:
            instance = await mythic.login(
                server_ip=config.server_url,
                username=config.username,
                password=config.password,
                timeout=config.timeout,
            )
    except Exception as e:
        pytest.skip(f"Mythic server unreachable: {e}")

    return instance
