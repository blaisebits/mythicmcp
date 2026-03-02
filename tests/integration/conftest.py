"""Integration test fixtures for MythicMCP.

Provides session-scoped fixtures for config loading and Mythic connection.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pytest

from tests.integration.config_models import IntegrationTestConfig, load_integration_config

_FIXTURE_FILE = Path(__file__).parent / "fixtures" / "test_upload.txt"


pytestmark = pytest.mark.integration


def _parse_server_url(server_url: str) -> tuple[str, int, bool]:
    """Parse a server URL into (host, port, ssl) for mythic.login().

    The mythic library expects server_ip as just the hostname/IP,
    with server_port and ssl as separate parameters.
    """
    parsed = urlparse(server_url)
    ssl = parsed.scheme == "https"
    host = parsed.hostname or server_url
    port = parsed.port or (7443 if ssl else 7080)
    return host, port, ssl


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
    host, port, ssl = _parse_server_url(config.server_url)

    try:
        if config.api_token:
            instance = await mythic.login(
                server_ip=host,
                server_port=port,
                ssl=ssl,
                apitoken=config.api_token,
                timeout=config.timeout,
            )
        else:
            instance = await mythic.login(
                server_ip=host,
                server_port=port,
                ssl=ssl,
                username=config.username,
                password=config.password,
                timeout=config.timeout,
            )
    except Exception as e:
        pytest.skip(f"Mythic server unreachable: {e}")

    return instance


@pytest.fixture(scope="session")
async def test_file_id(mythic_instance):
    """Upload test fixture file to Mythic and return its file_id.

    This file_id replaces REPLACE_WITH_FILE_ID placeholders in test commands.
    """
    from mythic import mythic

    if not _FIXTURE_FILE.exists():
        pytest.skip(f"Test fixture not found: {_FIXTURE_FILE}")

    file_id = await mythic.register_file(
        mythic_instance,
        filename=_FIXTURE_FILE.name,
        contents=_FIXTURE_FILE.read_bytes(),
    )
    assert file_id, "register_file returned empty file_id"
    return file_id
