"""Unit tests for mythicmcp.tools.callbacks module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.lab_config import (
    CALLBACK_ALT_IP,
    CALLBACK_EXTERNAL_IP,
    CALLBACK_INTERNAL_IP,
    CALLBACK_SECONDARY_IP,
)
from mythicmcp.tools.callbacks import (
    CallbackError,
    CallbackNotFoundError,
    NoOperationSetError,
    _parse_callback_detail,
    _parse_callback_summary,
    _format_time_since_last_checkin,
    core_get_callback,
    core_list_callbacks,
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
            "ip": CALLBACK_INTERNAL_IP,
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
        assert result.callback_id == 1
        assert result.hostname == "WORKSTATION-01"
        assert result.username == "john.doe"
        assert result.agent_type == "apollo"
        assert result.os == "Windows 10"
        assert result.internal_ip == CALLBACK_INTERNAL_IP
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
            "ip": CALLBACK_ALT_IP,
            "integrity_level": 0,
            "process_name": "bash",
            "active": True,
        }
        result = _parse_callback_summary(data)
        assert result.agent_type == ""

    def test_parse_empty_data_uses_defaults(self):
        """Handles empty data with defaults."""
        result = _parse_callback_summary({})
        assert result.callback_id == 0
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
            "ip": CALLBACK_INTERNAL_IP,
            "external_ip": CALLBACK_EXTERNAL_IP,
            "os": "Windows 10",
            "architecture": "x64",
            "pid": 1234,
            "process_name": "explorer.exe",
            "integrity_level": 3,
            "description": "Initial callback",
            "sleep_info": "10 23",
            "last_checkin": "2026-04-21T19:00:00Z",
            "active": True,
            "payload": {
                "payloadtype": {
                    "name": "apollo"
                }
            }
        }
        result = _parse_callback_detail(data)
        assert result.domain == "CORP"
        assert result.external_ip == CALLBACK_EXTERNAL_IP
        assert result.architecture == "x64"
        assert result.process_id == 1234
        assert result.description == "Initial callback"
        assert result.sleep_info == "10 23"
        assert result.last_checkin == "2026-04-21T19:00:00Z"


class TestTimeSinceLastCheckin:
    """Tests for synthetic callback timing fields."""

    def test_formats_elapsed_time(self):
        with patch("mythicmcp.tools.callbacks.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2026, 4, 21, 20, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

            result = _format_time_since_last_checkin("2026-04-21T19:58:45Z")

            assert result == "1m 15s"

    def test_handles_missing_value(self):
        assert _format_time_since_last_checkin(None) is None

    def test_handles_invalid_value(self):
        assert _format_time_since_last_checkin("not-a-time") is None

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
                "ip": CALLBACK_ALT_IP,
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
                "ip": CALLBACK_SECONDARY_IP,
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
                    "ip": CALLBACK_INTERNAL_IP,
                    "external_ip": CALLBACK_EXTERNAL_IP,
                    "os": "Windows 10",
                    "architecture": "x64",
                    "pid": 1234,
                    "process_name": "explorer.exe",
                    "integrity_level": 3,
                    "description": "Initial callback",
                    "sleep_info": "10 23",
                    "last_checkin": "2026-04-21T19:00:00Z",
                    "active": True,
                    "payload": {"payloadtype": {"name": "apollo"}}
                }
            ]
        }

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = callback_data

            result = await get_callback_by_id(mock_mythic, 1)

            assert result.callback.callback_id == 1
            assert result.callback.hostname == "WORKSTATION-01"
            assert result.callback.domain == "CORP"
            assert result.callback.sleep_info == "10 23"
            assert result.callback.last_checkin == "2026-04-21T19:00:00Z"
            assert result.callback.time_since_last_checkin is not None

    @pytest.mark.asyncio
    async def test_raises_error_when_callback_not_found(self):
        """Raises CallbackNotFoundError when callback doesn't exist."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"callback": []}

            with pytest.raises(CallbackNotFoundError, match="not found"):
                await get_callback_by_id(mock_mythic, 999)


class TestCallbackDocstrings:
    """Tool docs should teach callback_id semantics directly."""

    def test_list_callbacks_docstring_mentions_callback_id(self):
        assert "callback_id" in (core_list_callbacks.__doc__ or "")
        assert "display_id" in (core_list_callbacks.__doc__ or "")

    def test_get_callback_docstring_mentions_callback_id(self):
        assert "callback_id" in (core_get_callback.__doc__ or "")
