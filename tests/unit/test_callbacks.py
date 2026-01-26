"""Unit tests for mythicmcp.tools.callbacks module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mythicmcp.tools.callbacks import (
    CallbackError,
    CallbackNotFoundError,
    NoOperationSetError,
    _parse_callback_detail,
    _parse_callback_summary,
    get_callback_by_id,
    list_callbacks,
)


class TestParseCallbackSummary:
    """Tests for _parse_callback_summary function."""

    def test_parse_full_callback_data(self):
        """Parses complete callback data correctly."""
        data = {
            "id": 1,
            "display_id": 1,
            "host": "WORKSTATION-01",
            "user": "john.doe",
            "os": "Windows 10",
            "ip": "192.168.1.50",
            "integrity_level": 3,
            "process_name": "explorer.exe",
            "active": True,
            "payload": {
                "payloadtype": {
                    "name": "apollo"
                }
            }
        }
        result = _parse_callback_summary(data)
        assert result.id == 1
        assert result.hostname == "WORKSTATION-01"
        assert result.username == "john.doe"
        assert result.agent_type == "apollo"
        assert result.os == "Windows 10"
        assert result.internal_ip == "192.168.1.50"
        assert result.integrity_level == 3
        assert result.process_name == "explorer.exe"
        assert result.active is True

    def test_parse_missing_payload(self):
        """Handles missing payload gracefully."""
        data = {
            "id": 1,
            "display_id": 1,
            "host": "HOST",
            "user": "user",
            "os": "Linux",
            "ip": "10.0.0.1",
            "integrity_level": 0,
            "process_name": "bash",
            "active": True,
        }
        result = _parse_callback_summary(data)
        assert result.agent_type == ""

    def test_parse_empty_data_uses_defaults(self):
        """Handles empty data with defaults."""
        result = _parse_callback_summary({})
        assert result.id == 0
        assert result.hostname == ""
        assert result.agent_type == ""


class TestParseCallbackDetail:
    """Tests for _parse_callback_detail function."""

    def test_parse_full_detail(self):
        """Parses complete callback detail data."""
        data = {
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
            "description": "Initial callback",
            "active": True,
            "payload": {
                "payloadtype": {
                    "name": "apollo"
                }
            }
        }
        result = _parse_callback_detail(data)
        assert result.domain == "CORP"
        assert result.external_ip == "203.0.113.50"
        assert result.architecture == "x64"
        assert result.process_id == 1234
        assert result.description == "Initial callback"


class TestListCallbacks:
    """Tests for list_callbacks function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        """Raises NoOperationSetError when no operation is set."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await list_callbacks(mock_mythic)

    @pytest.mark.asyncio
    async def test_returns_callbacks_list(self):
        """Returns ListCallbacksResponse with callbacks."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        callback_data = [
            {
                "id": 1,
                "display_id": 1,
                "host": "HOST1",
                "user": "user1",
                "os": "Windows",
                "ip": "10.0.0.1",
                "integrity_level": 2,
                "process_name": "cmd.exe",
                "active": True,
                "payload": {"payloadtype": {"name": "apollo"}}
            },
            {
                "id": 2,
                "display_id": 2,
                "host": "HOST2",
                "user": "user2",
                "os": "Linux",
                "ip": "10.0.0.2",
                "integrity_level": 0,
                "process_name": "bash",
                "active": True,
                "payload": {"payloadtype": {"name": "poseidon"}}
            },
        ]

        with patch("mythic.mythic.get_all_active_callbacks", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = callback_data

            result = await list_callbacks(mock_mythic)

            assert result.count == 2
            assert len(result.callbacks) == 2
            assert result.callbacks[0].hostname == "HOST1"
            assert result.callbacks[1].hostname == "HOST2"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_callbacks(self):
        """Returns empty list when no callbacks exist."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch("mythic.mythic.get_all_active_callbacks", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []

            result = await list_callbacks(mock_mythic)

            assert result.count == 0
            assert result.callbacks == []


class TestGetCallbackById:
    """Tests for get_callback_by_id function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        """Raises NoOperationSetError when no operation is set."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await get_callback_by_id(mock_mythic, 1)

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_id(self):
        """Raises CallbackNotFoundError for invalid callback ID."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with pytest.raises(CallbackNotFoundError, match="Invalid callback ID"):
            await get_callback_by_id(mock_mythic, 0)

        with pytest.raises(CallbackNotFoundError, match="Invalid callback ID"):
            await get_callback_by_id(mock_mythic, -1)

    @pytest.mark.asyncio
    async def test_returns_callback_detail(self):
        """Returns GetCallbackResponse with callback details."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        callback_data = {
            "callback": [
                {
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
                    "description": "Initial callback",
                    "active": True,
                    "payload": {"payloadtype": {"name": "apollo"}}
                }
            ]
        }

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = callback_data

            result = await get_callback_by_id(mock_mythic, 1)

            assert result.callback.id == 1
            assert result.callback.hostname == "WORKSTATION-01"
            assert result.callback.domain == "CORP"

    @pytest.mark.asyncio
    async def test_raises_error_when_callback_not_found(self):
        """Raises CallbackNotFoundError when callback doesn't exist."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"callback": []}

            with pytest.raises(CallbackNotFoundError, match="not found"):
                await get_callback_by_id(mock_mythic, 999)
