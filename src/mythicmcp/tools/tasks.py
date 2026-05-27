"""Task tools for MythicMCP.

Provides tools for inspecting Mythic tasks after the fact:
- core_get_task_output: Fetch all output responses for a task by display ID
- core_list_callback_tasks: List every task issued to a specific callback
- core_get_task_callback: Find which callback a task was issued to
- core_list_interactive_tasks: List interactive child tasks within a PTY session
- core_get_interactive_session: Reconstruct a full PTY session transcript
"""

from __future__ import annotations

import base64
import logging
import re
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    GetInteractiveSessionResponse,
    GetTaskCallbackResponse,
    GetTaskOutputResponse,
    InteractiveSessionEvent,
    InteractiveTaskEntry,
    ListCallbackTasksResponse,
    ListInteractiveTasksResponse,
    TaskCallbackInfo,
    TaskOutput,
    TaskSummary,
)

# Mythic interactive task type enum (from InteractiveTaskEnum.go, iota-based)
INTERACTIVE_TASK_TYPE_LABELS: dict[int, str] = {
    0: "Input",
    1: "Output",
    2: "Error",
    3: "Exit",
    4: "Escape",
    5: "CtrlA",
    6: "CtrlB",
    7: "CtrlC",
    8: "CtrlD",
    9: "CtrlE",
    10: "CtrlF",
    11: "CtrlG",
    12: "Backspace",
    13: "Tab",
    14: "CtrlK",
    15: "CtrlL",
    16: "CtrlN",
    17: "CtrlP",
    18: "CtrlQ",
    19: "CtrlR",
    20: "CtrlS",
    21: "CtrlU",
    22: "CtrlW",
    23: "CtrlY",
    24: "CtrlZ",
}


def _decode_interactive_type(raw: int | None) -> tuple[int, str]:
    """Decode an interactive_task_type integer to (raw, label).

    Args:
        raw: Integer from the Mythic task row, or None.

    Returns:
        Tuple of (integer value, human label). Unknown values become "Unknown(N)".
    """
    if raw is None:
        return (0, "Unknown")
    label = INTERACTIVE_TASK_TYPE_LABELS.get(raw, f"Unknown({raw})")
    return (raw, label)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


class TaskError(Exception):
    """Base exception for task operations."""

    pass


class TaskNotFoundError(TaskError):
    """Raised when a task cannot be located."""

    pass


class NoOperationSetError(TaskError):
    """Raised when no current operation is set in Mythic."""

    pass


def _decode_response_text(value: str | None) -> str:
    """Decode Mythic response_text like the UI does.

    Mythic stores task output in the GraphQL `response_text` field as base64.
    The React UI aliases that field to `response` and decodes it client-side
    before display. The Python SDK returns raw `response_text`, so MCP needs to
    decode it explicitly to match the UI.
    """
    if not value:
        return ""

    normalized = "".join(value.split())

    if not normalized or not re.fullmatch(r"[A-Za-z0-9+/=]+", normalized):
        return value

    try:
        raw = base64.b64decode(normalized)
        return raw.decode("utf-8")
    except Exception:
        return value


def _parse_task_summary(task_data: dict) -> TaskSummary:
    """Parse raw task data from Mythic into TaskSummary model.

    Args:
        task_data: Raw task dict from the SDK (task_fragment shape).

    Returns:
        TaskSummary model.
    """
    operator_name = ""
    if operator := task_data.get("operator"):
        operator_name = operator.get("username", "")

    callback_id = 0
    callback_display_id = 0
    if callback := task_data.get("callback"):
        callback_id = callback.get("id", 0)
        callback_display_id = callback.get("display_id", 0)

    return TaskSummary(
        task_id=task_data.get("id", 0),
        task_display_id=task_data.get("display_id", 0),
        command_name=task_data.get("command_name", ""),
        status=task_data.get("status", ""),
        completed=bool(task_data.get("completed", False)),
        timestamp=task_data.get("timestamp"),
        operator=operator_name,
        original_params=task_data.get("original_params", "") or "",
        display_params=task_data.get("display_params", "") or "",
        callback_id=callback_id,
        display_id=callback_display_id,
    )


async def _resolve_callback_display_id(
    mythic_instance: mythic_classes.Mythic, callback_id: int
) -> tuple[int, int]:
    """Resolve a canonical callback_id to its current UI display_id."""
    from mythic import mythic

    query = """
    query ResolveCallbackDisplayId($callback_id: Int!) {
        callback(where: {id: {_eq: $callback_id}}, limit: 1) {
            id
            display_id
        }
    }
    """

    result = await mythic.execute_custom_query(
        mythic=mythic_instance,
        query=query,
        variables={"callback_id": callback_id},
    )

    callbacks = result.get("callback", []) if isinstance(result, dict) else []
    if not callbacks:
        raise TaskError(f"Callback with ID {callback_id} not found")

    callback = callbacks[0]
    return callback.get("id", callback_id), callback.get("display_id", 0)


async def get_task_output_by_display_id(
    mythic_instance: mythic_classes.Mythic, task_display_id: int
) -> GetTaskOutputResponse:
    """Fetch all output responses for a task from Mythic.

    Args:
        mythic_instance: Authenticated Mythic instance
        task_display_id: The task display ID to retrieve output for

    Returns:
        GetTaskOutputResponse with output entries. Returns an empty list
        if the task has no output yet or the task does not exist.

    Raises:
        NoOperationSetError: If no current operation is set
        TaskError: For other errors retrieving task output
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    try:
        output_data = await mythic.get_all_task_output_by_id(
            mythic=mythic_instance,
            task_display_id=task_display_id,
        )

        outputs = [
            TaskOutput(
                response_id=item.get("id", 0),
                response=_decode_response_text(item.get("response_text", "")),
                timestamp=item.get("timestamp"),
            )
            for item in output_data
        ]

        return GetTaskOutputResponse(
            task_display_id=task_display_id,
            output=outputs,
            count=len(outputs),
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise TaskError(
            f"Failed to retrieve task output: {type(e).__name__}"
        ) from e


async def list_tasks_by_callback(
    mythic_instance: mythic_classes.Mythic, callback_id: int
) -> ListCallbackTasksResponse:
    """Fetch all tasks issued to a specific callback.

    Args:
        mythic_instance: Authenticated Mythic instance.
        callback_id: Canonical callback_id to filter tasks by.

    Returns:
        ListCallbackTasksResponse with tasks sorted as returned by Mythic.

    Raises:
        NoOperationSetError: If no current operation is set.
        TaskError: For other errors retrieving tasks.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    try:
        resolved_callback_id, callback_display_id = await _resolve_callback_display_id(
            mythic_instance, callback_id
        )
        tasks_data = await mythic.get_all_tasks(
            mythic=mythic_instance,
            callback_display_id=callback_display_id,
        )

        tasks = [_parse_task_summary(t) for t in tasks_data]

        return ListCallbackTasksResponse(
            callback_id=resolved_callback_id,
            display_id=callback_display_id,
            tasks=tasks,
            count=len(tasks),
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise TaskError(
            f"Failed to list tasks for callback: {type(e).__name__}"
        ) from e


async def get_callback_for_task(
    mythic_instance: mythic_classes.Mythic, task_display_id: int
) -> GetTaskCallbackResponse:
    """Find the callback a task was issued to.

    Args:
        mythic_instance: Authenticated Mythic instance.
        task_display_id: The task display ID to look up.

    Returns:
        GetTaskCallbackResponse with task metadata and callback identifiers.

    Raises:
        NoOperationSetError: If no current operation is set.
        TaskNotFoundError: If the task does not exist.
        TaskError: For other errors retrieving the task.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    if task_display_id <= 0:
        raise TaskNotFoundError(f"Invalid task display ID: {task_display_id}")

    query = """
    query GetTaskCallback($task_display_id: Int!) {
        task(where: {display_id: {_eq: $task_display_id}}) {
            id
            display_id
            command_name
            status
            callback {
                id
                display_id
                host
                user
                payload {
                    payloadtype {
                        name
                    }
                }
            }
        }
    }
    """

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=query,
            variables={"task_display_id": task_display_id},
        )

        tasks = result.get("task", []) if isinstance(result, dict) else []
        if not tasks:
            raise TaskNotFoundError(
                f"Task with display ID {task_display_id} not found"
            )

        task = tasks[0]
        callback_data = task.get("callback") or {}

        agent_type = ""
        if payload := callback_data.get("payload"):
            if payloadtype := payload.get("payloadtype"):
                agent_type = payloadtype.get("name", "")

        callback_info = TaskCallbackInfo(
            callback_id=callback_data.get("id", 0),
            display_id=callback_data.get("display_id", 0),
            hostname=callback_data.get("host", "") or "",
            username=callback_data.get("user", "") or "",
            agent_type=agent_type,
        )

        return GetTaskCallbackResponse(
            task_id=task.get("id", 0),
            task_display_id=task.get("display_id", task_display_id),
            command_name=task.get("command_name", ""),
            status=task.get("status", ""),
            callback=callback_info,
        )

    except TaskNotFoundError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise TaskError(
            f"Failed to retrieve callback for task: {type(e).__name__}"
        ) from e


_INTERACTIVE_TASKS_QUERY = """
query ListInteractiveTasks($parent_display_id: Int!) {
    task(where: {display_id: {_eq: $parent_display_id}}, limit: 1) {
        id
        display_id
        command_name
        is_interactive_task
        timestamp
        callback { id display_id }
        tasks(where: {is_interactive_task: {_eq: true}}, order_by: {timestamp: asc}) {
            id
            display_id
            interactive_task_type
            original_params
            display_params
            status
            timestamp
            command_name
        }
    }
}
"""

_INTERACTIVE_SESSION_QUERY = """
query GetInteractiveSession($parent_display_id: Int!) {
    task(where: {display_id: {_eq: $parent_display_id}}, limit: 1) {
        id
        display_id
        command_name
        is_interactive_task
        timestamp
        callback { id display_id }
        responses(order_by: {id: asc}) {
            id
            response_text
            timestamp
        }
        tasks(where: {is_interactive_task: {_eq: true}}, order_by: {timestamp: asc}) {
            id
            display_id
            interactive_task_type
            original_params
            display_params
            status
            timestamp
            command_name
        }
    }
}
"""


async def list_interactive_tasks(
    mythic_instance: mythic_classes.Mythic, parent_task_display_id: int
) -> ListInteractiveTasksResponse:
    """List interactive child tasks of a PTY session.

    Args:
        mythic_instance: Authenticated Mythic instance.
        parent_task_display_id: Display ID of the parent PTY task.

    Returns:
        ListInteractiveTasksResponse with decoded interactive entries.

    Raises:
        NoOperationSetError: If no current operation is set.
        TaskNotFoundError: If the parent task does not exist.
        TaskError: For other errors.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    if parent_task_display_id <= 0:
        raise TaskNotFoundError(
            f"Invalid task display ID: {parent_task_display_id}"
        )

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=_INTERACTIVE_TASKS_QUERY,
            variables={"parent_display_id": parent_task_display_id},
        )

        tasks = result.get("task", []) if isinstance(result, dict) else []
        if not tasks:
            raise TaskNotFoundError(
                f"Task with display ID {parent_task_display_id} not found"
            )

        parent = tasks[0]
        children = parent.get("tasks", [])

        entries = []
        for child in children:
            raw_type, label = _decode_interactive_type(
                child.get("interactive_task_type")
            )
            entries.append(
                InteractiveTaskEntry(
                    id=child.get("id", 0),
                    display_id=child.get("display_id", 0),
                    interactive_task_type=raw_type,
                    interactive_task_type_label=label,
                    original_params=child.get("original_params", "") or "",
                    display_params=child.get("display_params", "") or "",
                    status=child.get("status", ""),
                    timestamp=child.get("timestamp"),
                    command_name=child.get("command_name", ""),
                )
            )

        return ListInteractiveTasksResponse(
            parent_task_display_id=parent_task_display_id,
            parent_command_name=parent.get("command_name", ""),
            entries=entries,
            count=len(entries),
        )

    except (TaskNotFoundError, NoOperationSetError):
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise TaskError(
            f"Failed to list interactive tasks: {type(e).__name__}"
        ) from e


async def get_interactive_session(
    mythic_instance: mythic_classes.Mythic, parent_task_display_id: int
) -> GetInteractiveSessionResponse:
    """Reconstruct a full interactive PTY session transcript.

    Fetches every interactive child task and its response rows, then stitches
    them into a chronological event list of inputs, outputs, and control events.

    Args:
        mythic_instance: Authenticated Mythic instance.
        parent_task_display_id: Display ID of the parent PTY task.

    Returns:
        GetInteractiveSessionResponse with interleaved events.

    Raises:
        NoOperationSetError: If no current operation is set.
        TaskNotFoundError: If the parent task does not exist.
        TaskError: For other errors.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    if parent_task_display_id <= 0:
        raise TaskNotFoundError(
            f"Invalid task display ID: {parent_task_display_id}"
        )

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=_INTERACTIVE_SESSION_QUERY,
            variables={"parent_display_id": parent_task_display_id},
        )

        tasks = result.get("task", []) if isinstance(result, dict) else []
        if not tasks:
            raise TaskNotFoundError(
                f"Task with display ID {parent_task_display_id} not found"
            )

        parent = tasks[0]
        children = parent.get("tasks", [])

        callback_data = parent.get("callback") or {}
        callback_id = callback_data.get("id", 0)
        callback_display_id = callback_data.get("display_id", 0)

        parent_display_id = parent.get("display_id", parent_task_display_id)

        # Collect input/control events from child interactive tasks
        events: list[InteractiveSessionEvent] = []
        for child in children:
            _raw_type, label = _decode_interactive_type(
                child.get("interactive_task_type")
            )
            events.append(
                InteractiveSessionEvent(
                    task_display_id=child.get("display_id", 0),
                    event_type=label,
                    content=child.get("original_params", "") or "",
                    timestamp=child.get("timestamp"),
                )
            )

        # Collect terminal output from the PARENT task's response rows.
        # Mythic stores interactive output on the parent pty task, not
        # on the individual child input tasks.
        for resp in parent.get("responses", []):
            events.append(
                InteractiveSessionEvent(
                    task_display_id=parent_display_id,
                    event_type="Output",
                    content=_decode_response_text(resp.get("response_text", "")),
                    timestamp=resp.get("timestamp"),
                )
            )

        # Sort all events chronologically so inputs and outputs interleave.
        # Parse timestamps rather than comparing strings, since fractional
        # seconds (e.g. "12:00:01.5Z") sort incorrectly lexicographically.
        def _sort_key(e: InteractiveSessionEvent) -> str:
            ts = e.timestamp or ""
            # Pad timestamps without fractional seconds so they sort correctly
            # e.g. "...01Z" → "...01.000000Z" to sort before "...01.5Z"
            if ts.endswith("Z") and "." not in ts:
                ts = ts[:-1] + ".000000Z"
            return ts

        events.sort(key=_sort_key)

        return GetInteractiveSessionResponse(
            parent_task_display_id=parent_task_display_id,
            parent_command_name=parent.get("command_name", ""),
            callback_id=callback_id,
            display_id=callback_display_id,
            events=events,
            event_count=len(events),
        )

    except (TaskNotFoundError, NoOperationSetError):
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise TaskError(
            f"Failed to retrieve interactive session: {type(e).__name__}"
        ) from e


async def core_get_task_output(
    ctx: Context, task_display_id: int
) -> GetTaskOutputResponse:
    """Retrieve all output responses for a task by its display ID.

    Returns every output chunk Mythic has recorded for the task, in the order
    they were received. Useful for inspecting long-running or previously-issued
    tasks without re-executing them.

    Args:
        task_display_id: The task display ID to fetch output for (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_task_output_by_display_id(
            mythic_ctx.mythic, task_display_id
        )
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_task_output")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )


async def core_list_callback_tasks(
    ctx: Context, callback_id: int
) -> ListCallbackTasksResponse:
    """List every task issued to a specific Mythic callback.

    Returns task metadata (command name, status, parameters, operator, timestamp)
    for every task recorded against the given callback. Use this to review what
    has already been run on a callback before issuing new work. Returned task
    objects include canonical `callback_id` plus UI-only `display_id`.

    Args:
        callback_id: Canonical callback_id to list tasks for (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_tasks_by_callback(mythic_ctx.mythic, callback_id)
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_callback_tasks")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )


async def core_get_task_callback(
    ctx: Context, task_display_id: int
) -> GetTaskCallbackResponse:
    """Find the callback that a Mythic task was issued to.

    Returns the task's command and status along with the associated callback's
    canonical `callback_id`, UI-only `display_id`, hostname, user context, and
    agent type. Use `callback_id` for all follow-on callback references.

    Args:
        task_display_id: The task display ID to look up (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_callback_for_task(mythic_ctx.mythic, task_display_id)
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_task_callback")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )


async def core_list_interactive_tasks(
    ctx: Context, parent_task_display_id: int
) -> ListInteractiveTasksResponse:
    """List interactive child tasks within a Mythic PTY session.

    Given the display ID of a parent PTY task (e.g. from poseidon_pty), returns
    every interactive child task in chronological order with its decoded type
    label (Input, CtrlC, Exit, etc.) and parameters.

    Note: terminal output for interactive sessions is stored on the PARENT task,
    not individual child tasks. Use core_get_task_output with the parent task's
    display ID to retrieve session output, or use core_get_interactive_session
    for a fully interleaved transcript.

    Args:
        parent_task_display_id: The PTY parent task display ID (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_interactive_tasks(
            mythic_ctx.mythic, parent_task_display_id
        )
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_interactive_tasks")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )


async def core_get_interactive_session(
    ctx: Context, parent_task_display_id: int
) -> GetInteractiveSessionResponse:
    """Reconstruct a full PTY session transcript from a Mythic interactive task.

    Given the display ID of a parent PTY task, fetches all interactive child
    tasks and their terminal output, then returns a chronological event list
    interleaving inputs, control sequences, and terminal output. Use this for
    a complete session replay; use core_list_interactive_tasks if you only need
    the task list without response data.

    Args:
        parent_task_display_id: The PTY parent task display ID (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_interactive_session(
            mythic_ctx.mythic, parent_task_display_id
        )
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except TaskError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_interactive_session")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )
