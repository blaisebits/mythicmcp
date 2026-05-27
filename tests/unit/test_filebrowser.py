"""Unit tests for mythicmcp.tools.filebrowser module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mythicmcp.tools.filebrowser import (
    FileBrowserError,
    NoOperationSetError,
    _extract_permissions,
    _parse_file_browser_entry,
    get_file_browser_by_task,
    list_file_browser,
)


class TestExtractPermissions:
    """Tests for _extract_permissions helper."""

    def test_none_returns_empty(self):
        assert _extract_permissions(None) == ""

    def test_string_passthrough(self):
        assert _extract_permissions("rwxr-xr-x") == "rwxr-xr-x"

    def test_dict_serialized_to_json(self):
        result = _extract_permissions({"user": "rwx", "group": "r-x"})
        assert '"user"' in result
        assert '"rwx"' in result

    def test_other_types_stringified(self):
        assert _extract_permissions(755) == "755"


class TestParseFileBrowserEntry:
    """Tests for _parse_file_browser_entry helper."""

    def test_parses_full_entry(self):
        data = {
            "id": 42,
            "name_text": "passwd",
            "full_path_text": "/etc/passwd",
            "parent_path_text": "/etc",
            "host": "web-01",
            "can_have_children": False,
            "has_children": False,
            "metadata": {
                "size": 2048,
                "permissions": "rw-r--r--",
                "access_time": "2026-04-10T10:00:00Z",
                "modify_time": "2026-03-15T08:30:00Z",
            },
            "comment": "interesting",
            "success": True,
            "timestamp": "2026-04-10T12:00:00Z",
            "tree_type": "file",
        }
        result = _parse_file_browser_entry(data)
        assert result.id == 42
        assert result.name == "passwd"
        assert result.full_path == "/etc/passwd"
        assert result.parent_path == "/etc"
        assert result.host == "web-01"
        assert result.is_file is True  # can_have_children=False → is_file=True
        assert result.size == 2048
        assert result.permissions == "rw-r--r--"
        assert result.access_time == "2026-04-10T10:00:00Z"
        assert result.modify_time == "2026-03-15T08:30:00Z"
        assert result.comment == "interesting"
        assert result.success is True

    def test_parses_directory_entry(self):
        data = {
            "id": 10,
            "name_text": "etc",
            "full_path_text": "/etc",
            "parent_path_text": "/",
            "host": "web-01",
            "can_have_children": True,
            "has_children": True,
            "metadata": {},
        }
        result = _parse_file_browser_entry(data)
        assert result.is_file is False  # can_have_children=True → is_file=False
        assert result.size is None

    def test_handles_missing_fields(self):
        result = _parse_file_browser_entry({})
        assert result.id == 0
        assert result.name == ""
        assert result.full_path == ""
        assert result.is_file is True
        assert result.size is None
        assert result.permissions == ""

    def test_handles_none_text_fields(self):
        data = {
            "id": 1,
            "name_text": None,
            "full_path_text": None,
            "parent_path_text": None,
            "host": None,
            "metadata": None,
            "comment": None,
        }
        result = _parse_file_browser_entry(data)
        assert result.name == ""
        assert result.full_path == ""
        assert result.parent_path == ""
        assert result.host == ""
        assert result.permissions == ""
        assert result.comment == ""

    def test_handles_metadata_as_json_string(self):
        data = {
            "id": 1,
            "metadata": '{"size": 1024, "permissions": "rwx"}',
        }
        result = _parse_file_browser_entry(data)
        assert result.size == 1024
        assert result.permissions == "rwx"

    def test_handles_dict_permissions_in_metadata(self):
        data = {
            "id": 1,
            "metadata": {"permissions": {"user": "rwx", "group": "r-x", "other": "r--"}},
        }
        result = _parse_file_browser_entry(data)
        assert '"user"' in result.permissions


class TestGetFileBrowserByTask:
    """Tests for get_file_browser_by_task function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await get_file_browser_by_task(mock_mythic, 38)

    @pytest.mark.asyncio
    async def test_returns_entries_for_task(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        query_result = {
            "mythictree": [
                {
                    "id": 1,
                    "name_text": "passwd",
                    "full_path_text": "/etc/passwd",
                    "parent_path_text": "/etc",
                    "host": "web-01",
                    "can_have_children": False,
                    "metadata": {"size": 2048, "permissions": "rw-r--r--"},
                    "comment": "",
                    "success": True,
                    "timestamp": "2026-04-10T12:00:00Z",
                },
                {
                    "id": 2,
                    "name_text": "shadow",
                    "full_path_text": "/etc/shadow",
                    "parent_path_text": "/etc",
                    "host": "web-01",
                    "can_have_children": False,
                    "metadata": {"size": 1024, "permissions": "rw-------"},
                    "comment": "",
                    "success": True,
                    "timestamp": "2026-04-10T12:00:00Z",
                },
            ]
        }

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = query_result

            result = await get_file_browser_by_task(mock_mythic, 38)

            assert result.task_display_id == 38
            assert result.count == 2
            assert result.entries[0].name == "passwd"
            assert result.entries[0].full_path == "/etc/passwd"
            assert result.entries[0].size == 2048
            assert result.entries[1].name == "shadow"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_entries(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"mythictree": []}

            result = await get_file_browser_by_task(mock_mythic, 99)

            assert result.count == 0
            assert result.entries == []

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.side_effect = RuntimeError("boom")

            with pytest.raises(FileBrowserError, match="Failed to retrieve.*boom"):
                await get_file_browser_by_task(mock_mythic, 38)


class TestListFileBrowser:
    """Tests for list_file_browser function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await list_file_browser(mock_mythic, "web-01")

    @pytest.mark.asyncio
    async def test_returns_entries_for_host(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        query_result = {
            "mythictree": [
                {
                    "id": 1,
                    "name_text": "etc",
                    "full_path_text": "/etc",
                    "parent_path_text": "/",
                    "host": "web-01",
                    "can_have_children": True,
                    "metadata": {},
                    "comment": "",
                    "success": True,
                    "timestamp": "2026-04-10T12:00:00Z",
                },
            ]
        }

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = query_result

            result = await list_file_browser(mock_mythic, "web-01")

            assert result.host == "web-01"
            assert result.path is None
            assert result.count == 1
            assert result.entries[0].name == "etc"
            assert result.entries[0].is_file is False

    @pytest.mark.asyncio
    async def test_filters_by_path(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"mythictree": []}

            result = await list_file_browser(mock_mythic, "web-01", path="/etc")

            assert result.host == "web-01"
            assert result.path == "/etc"
            call_kwargs = mock_q.await_args.kwargs
            assert call_kwargs["variables"]["path"] == "/etc"

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.side_effect = RuntimeError("boom")

            with pytest.raises(FileBrowserError, match="Failed to list.*boom"):
                await list_file_browser(mock_mythic, "web-01")
