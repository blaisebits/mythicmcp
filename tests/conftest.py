"""Shared pytest fixtures for MythicMCP tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.lab_config import CALLBACK_EXTERNAL_IP, CALLBACK_INTERNAL_IP


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load test environment from .env.test if it exists."""
    env_file = Path(__file__).parent.parent / ".env.test"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)


# Marker for tests that require a real Mythic server connection
requires_mythic = pytest.mark.skipif(
    not os.environ.get("MYTHIC_SERVER_URL"),
    reason="MYTHIC_SERVER_URL not set - skipping integration tests"
)

if TYPE_CHECKING:
    from mythicmcp.models import CallbackSummary


@pytest.fixture
def mock_mythic_instance() -> MagicMock:
    """Create a mock Mythic instance for testing."""
    mock = MagicMock()
    mock.current_operation_id = 1
    return mock


@pytest.fixture
def sample_callback_data() -> dict:
    """Sample callback data from Mythic GraphQL response."""
    return {
        "id": 1,
        "display_id": 1,
        "host": "WORKSTATION-01",
        "user": "john.doe",
        "domain": "CORP",
        "ip": CALLBACK_INTERNAL_IP,
        "external_ip": CALLBACK_EXTERNAL_IP,
        "os": "Windows 10",
        "architecture": "x64",
        "pid": 1234,
        "process_name": "explorer.exe",
        "integrity_level": 3,
        "description": "Initial callback from phishing",
        "active": True,
        "payload": {
            "payloadtype": {
                "name": "apollo"
            }
        }
    }


@pytest.fixture
def sample_operation_data() -> dict:
    """Sample operation data from Mythic GraphQL response."""
    return {
        "id": 1,
        "name": "Operation Sunrise",
        "created_at": "2026-01-20T08:00:00Z",
        "complete": False,
        "admin": {
            "id": 1,
            "username": "admin"
        }
    }


@pytest.fixture
def sample_operator_data() -> list[dict]:
    """Sample operator list from Mythic GraphQL response."""
    return [
        {"operator": {"username": "admin", "admin": True, "active": True}},
        {"operator": {"username": "operator1", "admin": False, "active": True}},
    ]


@pytest.fixture
def mock_mythic_context(mock_mythic_instance: MagicMock) -> MagicMock:
    """Create a mock MythicContext for tool testing."""
    from mythicmcp.connection import MythicContext

    context = MagicMock(spec=MythicContext)
    context.mythic = mock_mythic_instance
    return context
