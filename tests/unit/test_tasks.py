"""Unit tests for mythicmcp.tools.tasks module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mythicmcp.tools.tasks import (
    INTERACTIVE_TASK_TYPE_LABELS,
    NoOperationSetError,
    TaskError,
    TaskNotFoundError,
    _decode_interactive_type,
    _parse_task_summary,
    core_get_task_callback,
    core_list_callback_tasks,
    get_callback_for_task,
    get_interactive_session,
    get_task_output_by_display_id,
    list_interactive_tasks,
    list_tasks_by_callback,
)


class TestGetTaskOutputByDisplayId:
    """Tests for get_task_output_by_display_id function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        """Raises NoOperationSetError when no operation is set."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await get_task_output_by_display_id(mock_mythic, 42)

    @pytest.mark.asyncio
    async def test_returns_output_list(self):
        """Returns GetTaskOutputResponse populated with task output entries."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        output_data = [
            {
                "id": 101,
                "response_text": "bGluZSBvbmU=",
                "timestamp": "2026-04-08T12:00:00Z",
            },
            {
                "id": 102,
                "response_text": "bGluZSB0d28=",
                "timestamp": "2026-04-08T12:00:01Z",
            },
        ]

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = output_data

            result = await get_task_output_by_display_id(mock_mythic, 42)

            assert result.task_display_id == 42
            assert result.count == 2
            assert len(result.output) == 2
            assert result.output[0].response_id == 101
            assert result.output[0].response == "line one"
            assert result.output[1].response_id == 102
            assert result.output[1].response == "line two"

    @pytest.mark.asyncio
    async def test_falls_back_to_plaintext_when_response_is_not_base64(self):
        """Plaintext response_text values remain readable."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                {"id": 101, "response_text": "not-base64", "timestamp": "2026-04-08T12:00:00Z"}
            ]

            result = await get_task_output_by_display_id(mock_mythic, 42)

            assert result.output[0].response == "not-base64"

    @pytest.mark.asyncio
    async def test_decodes_wrapped_base64_response_text(self):
        """Base64 chunks with embedded newlines decode like the Mythic UI."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                {
                    "id": 101,
                    "response_text": "bGlu\nZSBv\nbmU=",
                    "timestamp": "2026-04-08T12:00:00Z",
                }
            ]

            result = await get_task_output_by_display_id(mock_mythic, 42)

            assert result.output[0].response == "line one"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_output(self):
        """Returns empty list when task has no output yet."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = []

            result = await get_task_output_by_display_id(mock_mythic, 99)

            assert result.task_display_id == 99
            assert result.count == 0
            assert result.output == []

    @pytest.mark.asyncio
    async def test_handles_missing_fields_with_defaults(self):
        """Handles output items with missing keys gracefully."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [{}]

            result = await get_task_output_by_display_id(mock_mythic, 1)

            assert result.count == 1
            assert result.output[0].response_id == 0
            assert result.output[0].response == ""
            assert result.output[0].timestamp is None

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors_as_task_error(self):
        """Non-operation errors from the Mythic SDK surface as TaskError."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = RuntimeError("boom")

            with pytest.raises(TaskError, match="Failed to retrieve task output"):
                await get_task_output_by_display_id(mock_mythic, 42)

    @pytest.mark.asyncio
    async def test_wraps_operation_errors_as_no_operation(self):
        """SDK errors mentioning 'operation' surface as NoOperationSetError."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = RuntimeError("no operation selected")

            with pytest.raises(NoOperationSetError):
                await get_task_output_by_display_id(mock_mythic, 42)


class TestParseTaskSummary:
    """Tests for _parse_task_summary helper."""

    def test_parses_full_task_data(self):
        """Flattens nested operator and callback fields."""
        data = {
            "id": 501,
            "display_id": 42,
            "command_name": "shell",
            "status": "completed",
            "completed": True,
            "timestamp": "2026-04-08T12:00:00Z",
            "operator": {"username": "blaise"},
            "original_params": "whoami",
            "display_params": "whoami",
            "callback": {"id": 7, "display_id": 3},
        }
        result = _parse_task_summary(data)
        assert result.task_id == 501
        assert result.task_display_id == 42
        assert result.command_name == "shell"
        assert result.status == "completed"
        assert result.completed is True
        assert result.operator == "blaise"
        assert result.callback_id == 7
        assert result.display_id == 3

    def test_handles_missing_nested_fields(self):
        """Missing operator/callback fall back to defaults."""
        result = _parse_task_summary({"id": 1, "display_id": 1})
        assert result.operator == ""
        assert result.callback_id == 0
        assert result.display_id == 0
        assert result.completed is False

    def test_handles_none_param_fields(self):
        """None values in param fields become empty strings."""
        result = _parse_task_summary(
            {"id": 1, "display_id": 1, "original_params": None, "display_params": None}
        )
        assert result.original_params == ""
        assert result.display_params == ""


class TestListTasksByCallback:
    """Tests for list_tasks_by_callback function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        """Raises NoOperationSetError when no operation is set."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await list_tasks_by_callback(mock_mythic, 3)

    @pytest.mark.asyncio
    async def test_returns_task_list(self):
        """Returns parsed tasks filtered by callback."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        tasks_data = [
            {
                "id": 101,
                "display_id": 10,
                "command_name": "shell",
                "status": "completed",
                "completed": True,
                "timestamp": "2026-04-08T12:00:00Z",
                "operator": {"username": "op1"},
                "original_params": "whoami",
                "display_params": "whoami",
                "callback": {"id": 5, "display_id": 3},
            },
            {
                "id": 102,
                "display_id": 11,
                "command_name": "ls",
                "status": "processing",
                "completed": False,
                "timestamp": "2026-04-08T12:01:00Z",
                "operator": {"username": "op1"},
                "original_params": "-la",
                "display_params": "-la",
                "callback": {"id": 5, "display_id": 3},
            },
        ]

        with patch(
            "mythicmcp.tools.tasks._resolve_callback_display_id",
            new_callable=AsyncMock,
        ) as mock_resolve, patch(
            "mythic.mythic.get_all_tasks", new_callable=AsyncMock
        ) as mock_get:
            mock_resolve.return_value = (5, 3)
            mock_get.return_value = tasks_data

            result = await list_tasks_by_callback(mock_mythic, 5)

            mock_resolve.assert_awaited_once_with(mock_mythic, 5)
            mock_get.assert_awaited_once()
            assert mock_get.await_args.kwargs["callback_display_id"] == 3
            assert result.callback_id == 5
            assert result.display_id == 3
            assert result.count == 2
            assert len(result.tasks) == 2
            assert result.tasks[0].command_name == "shell"
            assert result.tasks[1].status == "processing"
            assert result.tasks[0].display_id == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_tasks(self):
        """Returns empty task list when callback has no tasks."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythicmcp.tools.tasks._resolve_callback_display_id",
            new_callable=AsyncMock,
        ) as mock_resolve, patch(
            "mythic.mythic.get_all_tasks", new_callable=AsyncMock
        ) as mock_get:
            mock_resolve.return_value = (99, 17)
            mock_get.return_value = []

            result = await list_tasks_by_callback(mock_mythic, 99)

            assert result.count == 0
            assert result.tasks == []
            assert result.callback_id == 99
            assert result.display_id == 17

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors_as_task_error(self):
        """Unknown SDK errors surface as TaskError."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.get_all_tasks", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = RuntimeError("boom")

            with pytest.raises(TaskError, match="Failed to list tasks"):
                await list_tasks_by_callback(mock_mythic, 3)


class TestGetCallbackForTask:
    """Tests for get_callback_for_task function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        """Raises NoOperationSetError when no operation is set."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError, match="No current operation set"):
            await get_callback_for_task(mock_mythic, 42)

    @pytest.mark.asyncio
    async def test_raises_for_invalid_id(self):
        """Rejects non-positive task display IDs."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with pytest.raises(TaskNotFoundError, match="Invalid task display ID"):
            await get_callback_for_task(mock_mythic, 0)

    @pytest.mark.asyncio
    async def test_returns_callback_info(self):
        """Returns task and callback identifiers on success."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        query_result = {
            "task": [
                {
                    "id": 501,
                    "display_id": 42,
                    "command_name": "shell",
                    "status": "completed",
                    "callback": {
                        "id": 7,
                        "display_id": 3,
                        "host": "WIN-01",
                        "user": "alice",
                        "payload": {"payloadtype": {"name": "apollo"}},
                    },
                }
            ]
        }

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = query_result

            result = await get_callback_for_task(mock_mythic, 42)

            assert result.task_id == 501
            assert result.task_display_id == 42
            assert result.command_name == "shell"
            assert result.status == "completed"
            assert result.callback.callback_id == 7
            assert result.callback.display_id == 3
            assert result.callback.hostname == "WIN-01"
            assert result.callback.username == "alice"
            assert result.callback.agent_type == "apollo"

    @pytest.mark.asyncio
    async def test_raises_not_found_for_empty_result(self):
        """Empty task list surfaces as TaskNotFoundError."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": []}

            with pytest.raises(TaskNotFoundError, match="not found"):
                await get_callback_for_task(mock_mythic, 999)

    @pytest.mark.asyncio
    async def test_handles_missing_payload_gracefully(self):
        """Missing payload/payloadtype yields empty agent_type."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        query_result = {
            "task": [
                {
                    "id": 1,
                    "display_id": 1,
                    "command_name": "ls",
                    "status": "completed",
                    "callback": {
                        "id": 2,
                        "display_id": 2,
                        "host": "HOST",
                        "user": "root",
                    },
                }
            ]
        }

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = query_result

            result = await get_callback_for_task(mock_mythic, 1)
            assert result.callback.agent_type == ""

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors_as_task_error(self):
        """Unknown SDK errors surface as TaskError."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.side_effect = RuntimeError("boom")

            with pytest.raises(TaskError, match="Failed to retrieve callback"):
                await get_callback_for_task(mock_mythic, 42)


class TestTaskToolDocstrings:
    """Task tool docs should teach canonical callback_id usage."""

    def test_list_callback_tasks_docstring_mentions_callback_id(self):
        doc = core_list_callback_tasks.__doc__ or ""
        assert "callback_id" in doc
        assert "display_id" in doc

    def test_get_task_callback_docstring_mentions_callback_id(self):
        assert "callback_id" in (core_get_task_callback.__doc__ or "")


# --- Interactive / PTY tests ---


class TestDecodeInteractiveType:
    """Tests for _decode_interactive_type helper and enum mapping."""

    def test_known_types(self):
        """Decodes known enum values to labels."""
        assert _decode_interactive_type(0) == (0, "Input")
        assert _decode_interactive_type(1) == (1, "Output")
        assert _decode_interactive_type(3) == (3, "Exit")
        assert _decode_interactive_type(7) == (7, "CtrlC")
        assert _decode_interactive_type(24) == (24, "CtrlZ")

    def test_unknown_type(self):
        """Unknown values produce Unknown(N) label."""
        assert _decode_interactive_type(99) == (99, "Unknown(99)")

    def test_none_type(self):
        """None defaults to (0, 'Unknown')."""
        assert _decode_interactive_type(None) == (0, "Unknown")

    def test_enum_completeness(self):
        """Enum covers values 0-24 continuously."""
        assert len(INTERACTIVE_TASK_TYPE_LABELS) == 25
        for i in range(25):
            assert i in INTERACTIVE_TASK_TYPE_LABELS


_PARENT_TASK_DATA = {
    "id": 100,
    "display_id": 50,
    "command_name": "pty",
    "is_interactive_task": True,
    "timestamp": "2026-04-08T12:00:00Z",
    "callback": {"id": 5, "display_id": 3},
}

_CHILD_TASKS = [
    {
        "id": 201,
        "display_id": 51,
        "interactive_task_type": 0,
        "original_params": "whoami",
        "display_params": "whoami",
        "status": "completed",
        "timestamp": "2026-04-08T12:00:01Z",
        "command_name": "",
    },
    {
        "id": 202,
        "display_id": 52,
        "interactive_task_type": 7,
        "original_params": "",
        "display_params": "",
        "status": "completed",
        "timestamp": "2026-04-08T12:00:02Z",
        "command_name": "",
    },
]


class TestListInteractiveTasks:
    """Tests for list_interactive_tasks function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError):
            await list_interactive_tasks(mock_mythic, 50)

    @pytest.mark.asyncio
    async def test_raises_for_invalid_id(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with pytest.raises(TaskNotFoundError, match="Invalid"):
            await list_interactive_tasks(mock_mythic, 0)

    @pytest.mark.asyncio
    async def test_returns_decoded_entries(self):
        """Parses child tasks with decoded interactive type labels."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        parent = {**_PARENT_TASK_DATA, "tasks": _CHILD_TASKS}

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": [parent]}

            result = await list_interactive_tasks(mock_mythic, 50)

            assert result.parent_task_display_id == 50
            assert result.parent_command_name == "pty"
            assert result.count == 2
            assert result.entries[0].display_id == 51
            assert result.entries[0].interactive_task_type == 0
            assert result.entries[0].interactive_task_type_label == "Input"
            assert result.entries[0].original_params == "whoami"
            assert result.entries[1].interactive_task_type == 7
            assert result.entries[1].interactive_task_type_label == "CtrlC"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_children(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        parent = {**_PARENT_TASK_DATA, "tasks": []}

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": [parent]}

            result = await list_interactive_tasks(mock_mythic, 50)

            assert result.count == 0
            assert result.entries == []

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_parent(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": []}

            with pytest.raises(TaskNotFoundError, match="not found"):
                await list_interactive_tasks(mock_mythic, 999)


class TestGetInteractiveSession:
    """Tests for get_interactive_session function."""

    @pytest.mark.asyncio
    async def test_raises_error_when_no_operation_set(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = None

        with pytest.raises(NoOperationSetError):
            await get_interactive_session(mock_mythic, 50)

    @pytest.mark.asyncio
    async def test_raises_for_invalid_id(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with pytest.raises(TaskNotFoundError, match="Invalid"):
            await get_interactive_session(mock_mythic, 0)

    @pytest.mark.asyncio
    async def test_reconstructs_session_with_responses(self):
        """Interleaves input events with output from the parent task's responses."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        # Responses live on the PARENT task, not child tasks
        parent = {
            **_PARENT_TASK_DATA,
            "tasks": _CHILD_TASKS,
            "responses": [
                {
                    "id": 301,
                    "response_text": "cm9vdA==",
                    "timestamp": "2026-04-08T12:00:01.5Z",
                }
            ],
        }

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": [parent]}

            result = await get_interactive_session(mock_mythic, 50)

            assert result.parent_task_display_id == 50
            assert result.parent_command_name == "pty"
            assert result.callback_id == 5
            assert result.display_id == 3
            # Events are sorted chronologically:
            # 12:00:01Z  Input (whoami)
            # 12:00:01.5Z Output (root) — from parent responses
            # 12:00:02Z  CtrlC
            assert result.events[0].event_type == "Input"
            assert result.events[0].content == "whoami"
            assert result.events[0].task_display_id == 51
            assert result.events[1].event_type == "Output"
            assert result.events[1].content == "root"
            assert result.events[1].task_display_id == 50  # parent task
            assert result.events[2].event_type == "CtrlC"
            assert result.events[2].task_display_id == 52
            assert result.event_count == 3

    @pytest.mark.asyncio
    async def test_handles_empty_session(self):
        """Session with no child tasks and no responses returns empty event list."""
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        parent = {**_PARENT_TASK_DATA, "tasks": [], "responses": []}

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": [parent]}

            result = await get_interactive_session(mock_mythic, 50)

            assert result.event_count == 0
            assert result.events == []

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_parent(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.return_value = {"task": []}

            with pytest.raises(TaskNotFoundError, match="not found"):
                await get_interactive_session(mock_mythic, 999)

    @pytest.mark.asyncio
    async def test_wraps_sdk_errors(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 1

        with patch(
            "mythic.mythic.execute_custom_query", new_callable=AsyncMock
        ) as mock_q:
            mock_q.side_effect = RuntimeError("boom")

            with pytest.raises(TaskError, match="Failed to retrieve interactive"):
                await get_interactive_session(mock_mythic, 50)
