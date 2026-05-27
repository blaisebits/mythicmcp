"""Unit tests for Mythic connection status tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_check_connection_includes_accessible_operations(monkeypatch: pytest.MonkeyPatch):
    """Successful connection checks should include accessible operations."""
    from mythicmcp.models import ListOperationsResponse, OperationSummary
    from mythicmcp.tools.status import check_connection

    mock_mythic = MagicMock()
    mock_mythic.apitoken = "header.payload.signature"
    mock_mythic.current_operation_id = 1

    mock_ctx = MagicMock()
    mock_ctx.mythic = mock_mythic
    mock_ctx.config.safe_server_url = "https://mythic.local:7443"

    execute_custom_query = AsyncMock(side_effect=[
        {"operator": [{"username": "alice", "current_operation_id": 1}]},
        {"operation": [{"name": "Operation Sunrise"}]},
    ])

    monkeypatch.setattr("mythicmcp.tools.status._extract_user_id_from_token", lambda _: 1)
    monkeypatch.setattr("mythic.mythic.execute_custom_query", execute_custom_query)

    async def fake_list_operations(_mythic):
        return ListOperationsResponse(
            operations=[
                OperationSummary(
                    id=1,
                    name="Operation Sunrise",
                    complete=False,
                    admin_username="alice",
                ),
                OperationSummary(
                    id=2,
                    name="Operation Sunset",
                    complete=False,
                    admin_username="bob",
                ),
            ],
            count=2,
            current_operation_id=1,
        )

    monkeypatch.setattr("mythicmcp.tools.operations.list_operations", fake_list_operations)

    result = await check_connection(mock_ctx)

    assert result.connected is True
    assert result.current_operation == "Operation Sunrise"
    assert [op.name for op in result.accessible_operations] == [
        "Operation Sunrise",
        "Operation Sunset",
    ]
