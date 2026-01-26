"""Task execution for MythicMCP plugins.

Provides functions for executing Mythic commands via plugins
with agent type validation and timeout handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from mythicmcp.models import (
    CallbackAgentInfo,
    ExecuteTaskResponse,
    PluginToolErrorResponse,
    PluginToolSuccessResponse,
    TaskOutput,
    TaskStatus,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


class AgentTypeMismatchError(Exception):
    """Raised when callback's agent type doesn't match tool's required type.

    Attributes:
        expected: The agent type the tool requires.
        actual: The callback's actual agent type.
        callback_id: The callback ID that was checked.
    """

    def __init__(self, expected: str, actual: str, callback_id: int):
        self.expected = expected
        self.actual = actual
        self.callback_id = callback_id
        super().__init__(
            f"Agent type mismatch: tool requires '{expected}' but callback {callback_id} is '{actual}'"
        )


class CallbackNotFoundError(Exception):
    """Raised when a callback cannot be found."""

    def __init__(self, callback_id: int):
        self.callback_id = callback_id
        super().__init__(f"Callback with ID {callback_id} not found")


class CallbackInactiveError(Exception):
    """Raised when a callback is not active."""

    def __init__(self, callback_id: int):
        self.callback_id = callback_id
        super().__init__(f"Callback {callback_id} is not active")


class TaskExecutionError(Exception):
    """Raised when task execution fails."""

    def __init__(self, message: str, task_id: int | None = None):
        self.task_id = task_id
        super().__init__(message)


async def get_callback_agent_type(ctx: Context, callback_id: int) -> CallbackAgentInfo:
    """Get the agent type for a callback.

    Args:
        ctx: MCP context with Mythic connection.
        callback_id: The callback ID to look up.

    Returns:
        CallbackAgentInfo with agent type information.

    Raises:
        CallbackNotFoundError: If callback doesn't exist.
    """
    from mythic import mythic

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context
    mythic_instance = mythic_ctx.mythic

    query = """
    query GetCallbackAgentType($callback_id: Int!) {
        callback(where: {id: {_eq: $callback_id}}) {
            id
            active
            payload {
                payloadtype {
                    name
                }
            }
        }
    }
    """

    result = await mythic.execute_custom_query(
        mythic=mythic_instance,
        query=query,
        variables={"callback_id": callback_id},
    )

    callbacks = result.get("callback", [])
    if not callbacks:
        raise CallbackNotFoundError(callback_id)

    callback_data = callbacks[0]
    agent_type = ""
    if payload := callback_data.get("payload"):
        if payloadtype := payload.get("payloadtype"):
            agent_type = payloadtype.get("name", "")

    return CallbackAgentInfo(
        callback_id=callback_data.get("id", callback_id),
        agent_type=agent_type,
        active=callback_data.get("active", False),
    )


async def validate_agent_type(
    ctx: Context, callback_id: int, expected_agent_type: str
) -> CallbackAgentInfo:
    """Validate that a callback's agent type matches the expected type.

    Args:
        ctx: MCP context with Mythic connection.
        callback_id: The callback ID to validate.
        expected_agent_type: The agent type the tool requires.

    Returns:
        CallbackAgentInfo if validation passes.

    Raises:
        CallbackNotFoundError: If callback doesn't exist.
        CallbackInactiveError: If callback is not active.
        AgentTypeMismatchError: If agent type doesn't match.
    """
    callback_info = await get_callback_agent_type(ctx, callback_id)

    if not callback_info.active:
        raise CallbackInactiveError(callback_id)

    if callback_info.agent_type.lower() != expected_agent_type.lower():
        raise AgentTypeMismatchError(
            expected=expected_agent_type,
            actual=callback_info.agent_type,
            callback_id=callback_id,
        )

    return callback_info


async def execute_task(
    ctx: Context,
    callback_id: int,
    command_name: str,
    parameters: dict | None = None,
    timeout: int = 60,
) -> ExecuteTaskResponse:
    """Execute a task on a Mythic callback.

    Args:
        ctx: MCP context with Mythic connection.
        callback_id: Target callback ID.
        command_name: Command to execute.
        parameters: Command parameters (optional).
        timeout: Timeout in seconds (default 60).

    Returns:
        ExecuteTaskResponse with task results.

    Raises:
        TaskExecutionError: If task creation or execution fails.
        asyncio.TimeoutError: If task exceeds timeout.
    """
    from mythic import mythic

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context
    mythic_instance = mythic_ctx.mythic

    try:
        async with asyncio.timeout(timeout):
            # Issue task and wait for completion
            task = await mythic.issue_task(
                mythic=mythic_instance,
                command_name=command_name,
                parameters=parameters or {},
                callback_display_id=callback_id,
                wait_for_complete=True,
                timeout=timeout,
            )

            task_id = task.get("id", 0)
            task_display_id = task.get("display_id", 0)
            status_str = task.get("status", "").lower()

            # Map Mythic status to our TaskStatus
            if "complete" in status_str:
                status = TaskStatus.COMPLETED
            elif "error" in status_str:
                status = TaskStatus.ERROR
            elif "processing" in status_str:
                status = TaskStatus.PROCESSING
            else:
                status = TaskStatus.PENDING

            # Get task output
            output_list = await get_task_output(ctx, task_display_id)

            # Extract agent type from task
            agent_type = ""
            if callback := task.get("callback"):
                if payload := callback.get("payload"):
                    if payloadtype := payload.get("payloadtype"):
                        agent_type = payloadtype.get("name", "")

            return ExecuteTaskResponse(
                task_id=task_id,
                task_display_id=task_display_id,
                status=status,
                command=command_name,
                agent_type=agent_type,
                callback_id=callback_id,
                output=output_list,
                error=task.get("error") if status == TaskStatus.ERROR else None,
            )

    except asyncio.TimeoutError:
        logger.warning(f"Task execution timed out after {timeout}s for callback {callback_id}")
        raise


async def get_task_output(ctx: Context, task_display_id: int) -> list[TaskOutput]:
    """Get output for a completed task.

    Args:
        ctx: MCP context with Mythic connection.
        task_display_id: The task display ID.

    Returns:
        List of TaskOutput objects.
    """
    from mythic import mythic

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context
    mythic_instance = mythic_ctx.mythic

    try:
        output_data = await mythic.get_all_task_output_by_id(
            mythic=mythic_instance,
            task_display_id=task_display_id,
        )

        outputs = []
        for item in output_data:
            outputs.append(
                TaskOutput(
                    response_id=item.get("id", 0),
                    response=item.get("response", ""),
                    timestamp=item.get("timestamp"),
                )
            )
        return outputs

    except Exception as e:
        logger.warning(f"Failed to get task output for task {task_display_id}: {e}")
        return []


async def execute_with_validation(
    ctx: Context,
    callback_id: int,
    expected_agent_type: str,
    command_name: str,
    parameters: dict | None = None,
    timeout: int = 60,
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a task with agent type validation.

    This is the main entry point for plugin tool handlers. It validates
    the callback's agent type matches, then executes the task and
    returns a standardized response.

    Args:
        ctx: MCP context with Mythic connection.
        callback_id: Target callback ID.
        expected_agent_type: The agent type this tool requires.
        command_name: Mythic command to execute.
        parameters: Command parameters.
        timeout: Timeout in seconds.

    Returns:
        PluginToolSuccessResponse on success, PluginToolErrorResponse on failure.
    """
    start_time = time.perf_counter()

    try:
        # Validate agent type
        await validate_agent_type(ctx, callback_id, expected_agent_type)

        # Execute task
        result = await execute_task(
            ctx=ctx,
            callback_id=callback_id,
            command_name=command_name,
            parameters=parameters,
            timeout=timeout,
        )

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Check for execution errors
        if result.status == TaskStatus.ERROR:
            return PluginToolErrorResponse(
                error=result.error or "Task execution failed",
                error_type="execution_failed",
                callback_id=callback_id,
                task_id=result.task_id,
            )

        # Combine output responses
        output_text = "\n".join(o.response for o in result.output)

        return PluginToolSuccessResponse(
            task_id=result.task_id,
            output=output_text,
            execution_time_ms=execution_time_ms,
        )

    except CallbackNotFoundError as e:
        return PluginToolErrorResponse(
            error=str(e),
            error_type="callback_not_found",
            callback_id=callback_id,
        )

    except CallbackInactiveError as e:
        return PluginToolErrorResponse(
            error=str(e),
            error_type="callback_inactive",
            callback_id=callback_id,
        )

    except AgentTypeMismatchError as e:
        return PluginToolErrorResponse(
            error=str(e),
            error_type="agent_mismatch",
            callback_id=callback_id,
        )

    except asyncio.TimeoutError:
        return PluginToolErrorResponse(
            error=f"Command timed out after {timeout} seconds",
            error_type="timeout",
            callback_id=callback_id,
        )

    except Exception as e:
        logger.exception(f"Unexpected error executing task on callback {callback_id}")
        return PluginToolErrorResponse(
            error=f"Execution failed: {type(e).__name__}",
            error_type="execution_failed",
            callback_id=callback_id,
        )
