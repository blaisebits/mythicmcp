"""Shared pytest fixtures for MythicMCP tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

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
        "ip": "192.168.1.50",
        "external_ip": "203.0.113.50",
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
