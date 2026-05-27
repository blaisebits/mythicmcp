"""Generic callback-scoped command tools for MythicMCP.

Provides tools for listing, inspecting, and executing commands loaded on a
specific callback, including augment commands from external Mythic services.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import time
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    CallbackCommandDetail,
    CallbackCommandParameter,
    CallbackCommandSummary,
    ExecuteCallbackCommandErrorResponse,
    ExecuteCallbackCommandSuccessResponse,
    GetCallbackCommandResponse,
    ListCallbackCommandsResponse,
)
from mythicmcp.tools.tasks import _decode_response_text

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


LIST_CALLBACK_COMMANDS_QUERY = """
query ListCallbackCommands($callback_id: Int!) {
    callback_by_pk(id: $callback_id) {
        id
        display_id
        active
        payload {
            payloadtype {
                name
            }
        }
        loadedcommands(order_by: {command: {cmd: asc}}) {
            command {
                cmd
                help_cmd
                description
                attributes
                payloadtype {
                    name
                }
            }
        }
    }
}
"""


DETAIL_CALLBACK_COMMANDS_QUERY = """
query GetCallbackCommand($callback_id: Int!) {
    callback_by_pk(id: $callback_id) {
        id
        display_id
        active
        payload {
            payloadtype {
                name
            }
        }
        loadedcommands(order_by: {command: {cmd: asc}}) {
            command {
                cmd
                help_cmd
                description
                attributes
                payloadtype {
                    name
                }
                commandparameters(order_by: [{parameter_group_name: asc}, {ui_position: asc}]) {
                    name
                    cli_name
                    display_name
                    description
                    placeholder
                    example
                    type
                    default_value
                    required
                    parameter_group_name
                    ui_position
                    choices
                    choices_are_all_commands
                    choices_are_loaded_commands
                    choice_filter_by_command_attributes
                    supported_agents
                    supported_agent_build_parameters
                    dynamic_query_function
                }
            }
        }
    }
}
"""


DETAIL_CALLBACK_COMMANDS_QUERY_FALLBACK = """
query GetCallbackCommand($callback_id: Int!) {
    callback_by_pk(id: $callback_id) {
        id
        display_id
        active
        payload {
            payloadtype {
                name
            }
        }
        loadedcommands(order_by: {command: {cmd: asc}}) {
            command {
                cmd
                help_cmd
                description
                attributes
                payloadtype {
                    name
                }
                commandparameters(order_by: [{parameter_group_name: asc}, {ui_position: asc}]) {
                    name
                    cli_name
                    display_name
                    description
                    type
                    default_value
                    required
                    parameter_group_name
                    ui_position
                    choices
                    choices_are_all_commands
                    choices_are_loaded_commands
                    choice_filter_by_command_attributes
                    supported_agents
                    supported_agent_build_parameters
                    dynamic_query_function
                }
            }
        }
    }
}
"""

COMMAND_PARAMETERS_INTROSPECTION_QUERY = """
query CommandParametersType {
    __type(name: "commandparameters") {
        fields {
            name
        }
    }
}
"""

_OPTIONAL_PARAMETER_METADATA_SUPPORTED: bool | None = None


class CommandError(Exception):
    """Base exception for callback-command operations."""


class NoOperationSetError(CommandError):
    """Raised when no current operation is set in Mythic."""


class CallbackNotFoundError(CommandError):
    """Raised when a callback cannot be found."""


class AmbiguousCommandError(CommandError):
    """Raised when a command name resolves to multiple sources."""


class LoadedCommandNotFoundError(CommandError):
    """Raised when a command is not loaded on a callback."""


def _parse_command_summary(
    command_data: dict[str, Any], native_agent_type: str
) -> CallbackCommandSummary:
    """Parse a loaded command into a response summary."""
    source = ""
    if payloadtype := command_data.get("payloadtype"):
        source = payloadtype.get("name", "")

    return CallbackCommandSummary(
        command_name=command_data.get("cmd", ""),
        source=source,
        is_native=source == native_agent_type,
        usage=command_data.get("help_cmd", "") or "",
        description=command_data.get("description", "") or "",
        attributes=command_data.get("attributes") or {},
    )


def _parse_command_parameter(parameter_data: dict[str, Any]) -> CallbackCommandParameter:
    """Parse Mythic command parameter metadata."""
    return CallbackCommandParameter(
        name=parameter_data.get("name", "") or "",
        cli_name=parameter_data.get("cli_name", "") or "",
        display_name=parameter_data.get("display_name", "") or "",
        description=parameter_data.get("description", "") or "",
        placeholder=parameter_data.get("placeholder", "") or "",
        example=parameter_data.get("example", "") or "",
        type=parameter_data.get("type", "") or "",
        default_value=parameter_data.get("default_value", "") or "",
        required=bool(parameter_data.get("required", False)),
        parameter_group_name=parameter_data.get("parameter_group_name", "") or "",
        ui_position=parameter_data.get("ui_position", 0) or 0,
        choices=parameter_data.get("choices") or [],
        choices_are_all_commands=bool(
            parameter_data.get("choices_are_all_commands", False)
        ),
        choices_are_loaded_commands=bool(
            parameter_data.get("choices_are_loaded_commands", False)
        ),
        choice_filter_by_command_attributes=
        parameter_data.get("choice_filter_by_command_attributes") or {},
        supported_agents=parameter_data.get("supported_agents") or [],
        supported_agent_build_parameters=
        parameter_data.get("supported_agent_build_parameters") or {},
        dynamic_query_function=parameter_data.get("dynamic_query_function", "") or "",
    )


def _is_zero_arg_command(command_data: dict[str, Any]) -> bool:
    """Return True when Mythic help indicates a true zero-arg command."""
    help_cmd = (command_data.get("help_cmd") or "").strip()
    command_name = (command_data.get("cmd") or "").strip()
    return not help_cmd or help_cmd == command_name


def _derive_argument_mode(command_data: dict[str, Any]) -> str:
    """Derive the expected `arguments` shape from Mythic metadata."""
    if command_data.get("commandparameters"):
        return "json_object"
    return "cli"


def _build_example_arguments(command_data: dict[str, Any], argument_mode: str) -> str:
    """Build a compact example arguments string for the command."""
    if argument_mode == "json_object":
        if explicit_usage := _explicit_execution_usage(command_data):
            return explicit_usage

        required_params = [
            parameter
            for parameter in (command_data.get("commandparameters") or [])
            if parameter.get("required", False)
        ]
        payload = {
            (parameter.get("name", "") or ""): _example_value_for_parameter(parameter)
            for parameter in required_params
            if (parameter.get("name", "") or "")
        }
        return json.dumps(payload, separators=(",", ":"))

    if _is_zero_arg_command(command_data):
        return ""

    return "<raw command-line text>"


def _build_execution_usage(command_data: dict[str, Any], argument_mode: str) -> str:
    """Build the exact MCP `arguments` payload string to execute."""
    return _build_example_arguments(command_data, argument_mode)


def _build_execution_notes(argument_mode: str) -> str:
    """Build short execution guidance for the command."""
    if argument_mode == "json_object":
        return (
            "Usage may look CLI-style, but execution should pass a JSON object "
            "string keyed by parameter `name` values. Prefer "
            "`execution_usage` over `usage`; `example_arguments` should match "
            "it and only needs real target values swapped in."
        )

    return (
        "Execution should pass raw command-line text in `arguments`, or `\"\"` "
        "for a true zero-arg command."
    )


def _example_value_for_parameter(parameter_data: dict[str, Any]) -> Any:
    """Build a realistic starter value for one Mythic command parameter."""
    if explicit_value := _explicit_parameter_example_value(parameter_data):
        return explicit_value

    name = (parameter_data.get("name", "") or "").lower()
    display_name = (parameter_data.get("display_name", "") or "").lower()
    description = (parameter_data.get("description", "") or "").lower()
    param_type = (parameter_data.get("type", "") or "").lower()
    default_value = parameter_data.get("default_value", "")
    choices = parameter_data.get("choices") or []
    identity = " ".join(part for part in (name, display_name) if part)
    combined = " ".join(part for part in (identity, description) if part)

    if default_value not in ("", None):
        return default_value

    if choices:
        return choices[0]

    if any(token in identity for token in ("query",)):
        return "SELECT * FROM Win32_OperatingSystem"

    if "namespace" in identity:
        return r"root\cimv2"

    if "domain" in identity:
        return "example.local"

    if any(token in identity for token in ("host", "hostname", "server", "computer", "target")):
        return "10.0.0.5"

    if "port" in identity:
        return 445

    if any(token in identity for token in ("timeout", "sleep", "delay", "interval")):
        return 30

    if "bool" in param_type:
        return True

    if "query" in combined:
        return "SELECT * FROM Win32_OperatingSystem"

    if "namespace" in combined:
        return r"root\cimv2"

    if "domain" in combined:
        return "example.local"

    if any(token in combined for token in ("host", "hostname", "server", "computer", "target")):
        return "10.0.0.5"

    if "port" in combined:
        return 445

    if any(token in combined for token in ("timeout", "sleep", "delay", "interval")):
        return 30

    if any(token in combined for token in ("pid", "id", "count", "size")) and "string" not in param_type:
        return 1

    if any(token in identity for token in ("path", "file", "filename", "dll", "exe", "binary")):
        return r"C:\Windows\win.ini"

    if any(token in combined for token in ("path", "file", "filename", "dll", "exe", "binary")):
        return r"C:\Windows\win.ini"

    if any(token in param_type for token in ("number", "int", "integer")):
        return 1

    return f"<{parameter_data.get('name', 'value') or 'value'}>"


def _explicit_execution_usage(command_data: dict[str, Any]) -> str:
    """Return a command-level example usage string when explicitly provided."""
    for key in ("execution_usage", "example_arguments", "example_usage", "example"):
        value = command_data.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()

    attributes = command_data.get("attributes") or {}
    for key in ("execution_usage", "example_arguments", "example_usage", "example"):
        value = attributes.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _explicit_parameter_example_value(parameter_data: dict[str, Any]) -> str:
    """Prefer structured parameter examples over generic heuristics."""
    for key in ("placeholder", "example"):
        value = parameter_data.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()

    description = parameter_data.get("description", "")
    if isinstance(description, str):
        match = re.search(
            r"\bExamples?:\s*(.+?)(?=(?:\s+[A-Z][A-Za-z _-]+:)|$)",
            description,
        )
        if match:
            return match.group(1).strip()

    return ""


def _is_optional_parameter_metadata_error(exc: Exception) -> bool:
    """Return True when Mythic rejects newer commandparameter metadata fields."""
    try:
        from gql.transport.exceptions import TransportQueryError
    except Exception:
        TransportQueryError = ()  # type: ignore[assignment]

    if TransportQueryError and isinstance(exc, TransportQueryError):
        details = getattr(exc, "errors", None) or [str(exc)]
    else:
        details = [str(exc)]

    for detail in details:
        text = str(detail).lower()
        if "validation-failed" not in text:
            continue
        if "commandparameters" not in text:
            continue
        if "placeholder" in text or "example" in text:
            return True
    return False


async def _optional_parameter_metadata_supported(
    mythic_instance: mythic_classes.Mythic,
) -> bool:
    """Detect whether Mythic exposes richer commandparameter metadata fields."""
    global _OPTIONAL_PARAMETER_METADATA_SUPPORTED

    if _OPTIONAL_PARAMETER_METADATA_SUPPORTED is not None:
        return _OPTIONAL_PARAMETER_METADATA_SUPPORTED

    from mythic import mythic

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=COMMAND_PARAMETERS_INTROSPECTION_QUERY,
            variables={},
        )
    except Exception:
        _OPTIONAL_PARAMETER_METADATA_SUPPORTED = False
        return False

    fields = ((result or {}).get("__type") or {}).get("fields") or []
    names = {field.get("name", "") for field in fields if isinstance(field, dict)}
    _OPTIONAL_PARAMETER_METADATA_SUPPORTED = "placeholder" in names or "example" in names
    return _OPTIONAL_PARAMETER_METADATA_SUPPORTED


def _parse_task_timestamp(value: str | None) -> datetime | None:
    """Parse a Mythic task timestamp into an aware datetime when possible."""
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


async def _recover_recent_task(
    mythic_instance: mythic_classes.Mythic,
    callback_display_id: int,
    command_name: str,
    arguments: str,
    request_started_at: datetime,
) -> dict[str, Any] | None:
    """Best-effort recovery for a task created before wait_for_complete timed out."""
    from mythic import mythic

    tasks_data = await mythic.get_all_tasks(
        mythic=mythic_instance,
        callback_display_id=callback_display_id,
    )

    argument_text = (arguments or "").strip()
    cutoff = request_started_at - timedelta(seconds=30)
    candidates: list[dict[str, Any]] = []

    for task in tasks_data or []:
        if task.get("command_name") != command_name:
            continue

        timestamp = _parse_task_timestamp(task.get("timestamp"))
        if timestamp is not None and timestamp < cutoff:
            continue

        if argument_text:
            original_params = (task.get("original_params") or "").strip()
            display_params = (task.get("display_params") or "").strip()
            if original_params != argument_text and display_params != argument_text:
                continue

        candidates.append(task)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            _parse_task_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc),
            item.get("id", 0),
        ),
        reverse=True,
    )
    return candidates[0]


def _parse_command_detail(
    command_data: dict[str, Any], native_agent_type: str
) -> CallbackCommandDetail:
    """Parse a loaded command plus parameters into detail response."""
    summary = _parse_command_summary(command_data, native_agent_type)
    argument_mode = _derive_argument_mode(command_data)
    execution_usage = _build_execution_usage(command_data, argument_mode)
    return CallbackCommandDetail(
        **summary.model_dump(),
        parameters=[
            _parse_command_parameter(p)
            for p in (command_data.get("commandparameters") or [])
        ],
        argument_mode=argument_mode,
        execution_usage=execution_usage,
        example_arguments=execution_usage,
        zero_arg_example="" if argument_mode == "cli" and _is_zero_arg_command(command_data) else None,
        execution_notes=_build_execution_notes(argument_mode),
    )


async def _fetch_callback_commands(
    mythic_instance: mythic_classes.Mythic,
    callback_id: int,
    include_parameters: bool = False,
) -> dict[str, Any]:
    """Fetch loaded command metadata for a callback."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    if callback_id <= 0:
        raise CallbackNotFoundError(f"Invalid callback ID: {callback_id}")

    query = LIST_CALLBACK_COMMANDS_QUERY
    if include_parameters:
        supports_optional_metadata = await _optional_parameter_metadata_supported(
            mythic_instance
        )
        query = (
            DETAIL_CALLBACK_COMMANDS_QUERY
            if supports_optional_metadata
            else DETAIL_CALLBACK_COMMANDS_QUERY_FALLBACK
        )

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=query,
            variables={"callback_id": callback_id},
        )
    except Exception as exc:
        if not include_parameters or not _is_optional_parameter_metadata_error(exc):
            raise
        logger.info(
            "Retrying callback command query without optional placeholder/example metadata"
        )
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=DETAIL_CALLBACK_COMMANDS_QUERY_FALLBACK,
            variables={"callback_id": callback_id},
        )

    callback = result.get("callback_by_pk") if isinstance(result, dict) else None
    if not callback:
        raise CallbackNotFoundError(f"Callback with ID {callback_id} not found")
    return callback


def _filter_command_rows(
    loaded_commands: list[dict[str, Any]], source: str = ""
) -> list[dict[str, Any]]:
    """Filter raw loaded command rows by optional source."""
    filtered: list[dict[str, Any]] = []
    for row in loaded_commands:
        command = row.get("command") or {}
        command_source = ""
        if payloadtype := command.get("payloadtype"):
            command_source = payloadtype.get("name", "")
        if source and command_source != source:
            continue
        filtered.append(row)
    return filtered


def _resolve_loaded_command(
    loaded_commands: list[dict[str, Any]],
    command_name: str,
    source: str = "",
) -> dict[str, Any]:
    """Resolve one loaded command row, enforcing source disambiguation."""
    matches = []
    for row in loaded_commands:
        command = row.get("command") or {}
        if command.get("cmd") != command_name:
            continue
        if source:
            payloadtype = command.get("payloadtype") or {}
            if payloadtype.get("name") != source:
                continue
        matches.append(row)

    if not matches:
        if source:
            raise LoadedCommandNotFoundError(
                f"Command '{command_name}' from source '{source}' is not loaded on this callback"
            )
        raise LoadedCommandNotFoundError(
            f"Command '{command_name}' is not loaded on this callback"
        )

    if len(matches) > 1:
        candidates = sorted(
            {
                (row.get("command") or {}).get("payloadtype", {}).get("name", "")
                for row in matches
            }
        )
        raise AmbiguousCommandError(
            f"Command '{command_name}' is loaded from multiple sources: {', '.join(candidates)}. "
            "Specify source to disambiguate."
        )

    return matches[0]


async def list_callback_commands(
    mythic_instance: mythic_classes.Mythic,
    callback_id: int,
    source: str = "",
) -> ListCallbackCommandsResponse:
    """List commands loaded on a specific callback."""
    callback = await _fetch_callback_commands(mythic_instance, callback_id)

    native_agent_type = (
        ((callback.get("payload") or {}).get("payloadtype") or {}).get("name", "")
    )
    loaded_commands = _filter_command_rows(callback.get("loadedcommands") or [], source)
    commands = sorted(
        [
            _parse_command_summary(row.get("command") or {}, native_agent_type)
            for row in loaded_commands
        ],
        key=lambda item: (item.command_name, item.source),
    )

    return ListCallbackCommandsResponse(
        callback_id=callback.get("id", callback_id),
        display_id=callback.get("display_id", 0),
        agent_type=native_agent_type,
        source=source,
        commands=commands,
        count=len(commands),
    )


async def get_callback_command(
    mythic_instance: mythic_classes.Mythic,
    callback_id: int,
    command_name: str,
    source: str = "",
) -> GetCallbackCommandResponse:
    """Get detailed metadata for one loaded callback command."""
    callback = await _fetch_callback_commands(
        mythic_instance, callback_id, include_parameters=True
    )
    native_agent_type = (
        ((callback.get("payload") or {}).get("payloadtype") or {}).get("name", "")
    )
    resolved = _resolve_loaded_command(
        callback.get("loadedcommands") or [],
        command_name=command_name,
        source=source,
    )

    return GetCallbackCommandResponse(
        callback_id=callback.get("id", callback_id),
        display_id=callback.get("display_id", 0),
        agent_type=native_agent_type,
        command=_parse_command_detail(resolved.get("command") or {}, native_agent_type),
    )


async def execute_callback_command(
    mythic_instance: mythic_classes.Mythic,
    callback_id: int,
    command_name: str,
    arguments: str = "",
    source: str = "",
    timeout: int = 60,
) -> ExecuteCallbackCommandSuccessResponse | ExecuteCallbackCommandErrorResponse:
    """Execute a loaded callback command with a string `arguments` payload.

    `arguments` is not always raw CLI text. Some commands expect a raw command
    line, while others expect a JSON object string keyed by Mythic parameter
    names. Use `get_callback_command` to inspect `argument_mode`,
    `execution_usage`, `example_arguments`, and `execution_notes` before
    tasking.
    """
    from mythic import mythic

    start_time = time.perf_counter()

    try:
        callback = await _fetch_callback_commands(mythic_instance, callback_id)
        resolved_callback_id = callback.get("id", callback_id)
        callback_display_id = callback.get("display_id", 0)

        if not callback.get("active", False):
            return ExecuteCallbackCommandErrorResponse(
                error=f"Callback {resolved_callback_id} is not active",
                error_type="callback_inactive",
                callback_id=resolved_callback_id,
                display_id=callback_display_id,
                command_name=command_name,
            )

        resolved = _resolve_loaded_command(
            callback.get("loadedcommands") or [],
            command_name=command_name,
            source=source,
        )
        command = resolved.get("command") or {}
        command_source = ((command.get("payloadtype") or {}).get("name", "")) or source
        request_started_at = datetime.now(timezone.utc)

        try:
            async with asyncio.timeout(timeout):
                task = await mythic.issue_task(
                    mythic=mythic_instance,
                    command_name=command_name,
                    parameters=arguments or "",
                    callback_display_id=callback_display_id,
                    wait_for_complete=True,
                    timeout=timeout,
                    payload_type=command_source,
                )
        except asyncio.TimeoutError:
            recovered_task = await _recover_recent_task(
                mythic_instance,
                callback_display_id,
                command_name,
                arguments,
                request_started_at,
            )
            task_id = recovered_task.get("id", 0) if recovered_task else None
            task_display_id = (
                recovered_task.get("display_id", 0) if recovered_task else None
            )
            if task_id:
                return ExecuteCallbackCommandErrorResponse(
                    error=(
                        f"Command timed out after {timeout} seconds, but Mythic created "
                        f"task {task_display_id}. Inspect core_get_task_output next."
                    ),
                    error_type="timeout",
                    callback_id=resolved_callback_id,
                    display_id=callback_display_id,
                    command_name=command_name,
                    source=command_source,
                    task_id=task_id,
                    task_display_id=task_display_id,
                )
            return ExecuteCallbackCommandErrorResponse(
                error=f"Command timed out after {timeout} seconds",
                error_type="timeout",
                callback_id=resolved_callback_id,
                display_id=callback_display_id,
                command_name=command_name,
                source=command_source,
            )

        if not task or not task.get("display_id"):
            return ExecuteCallbackCommandErrorResponse(
                error=f"Command timed out after {timeout} seconds",
                error_type="timeout",
                callback_id=resolved_callback_id,
                display_id=callback_display_id,
                command_name=command_name,
                source=command_source,
            )

        task_id = task.get("id", 0)
        task_display_id = task.get("display_id", 0)
        status = (task.get("status") or "").lower()

        output_rows = await mythic.get_all_task_output_by_id(
            mythic=mythic_instance,
            task_display_id=task_display_id,
        )
        output_text = "\n".join(
            _decode_response_text(item.get("response_text", ""))
            for item in output_rows
            if _decode_response_text(item.get("response_text", ""))
        )

        if "error" in status:
            return ExecuteCallbackCommandErrorResponse(
                error=task.get("error") or "Task execution failed",
                error_type="execution_failed",
                callback_id=resolved_callback_id,
                display_id=callback_display_id,
                command_name=command_name,
                source=command_source,
                task_id=task_id,
                task_display_id=task_display_id,
            )

        return ExecuteCallbackCommandSuccessResponse(
            callback_id=resolved_callback_id,
            display_id=callback_display_id,
            command_name=command_name,
            source=command_source,
            task_id=task_id,
            task_display_id=task_display_id,
            output=output_text,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )

    except NoOperationSetError:
        raise
    except CallbackNotFoundError as e:
        return ExecuteCallbackCommandErrorResponse(
            error=str(e),
            error_type="callback_not_found",
            callback_id=callback_id,
            command_name=command_name,
            source=source or None,
        )
    except LoadedCommandNotFoundError as e:
        return ExecuteCallbackCommandErrorResponse(
            error=str(e),
            error_type="command_not_loaded",
            callback_id=callback_id,
            command_name=command_name,
            source=source or None,
        )
    except AmbiguousCommandError as e:
        return ExecuteCallbackCommandErrorResponse(
            error=str(e),
            error_type="ambiguous_command",
            callback_id=callback_id,
            command_name=command_name,
            source=source or None,
        )
    except Exception as e:
        logger.exception(
            "Unexpected error executing generic callback command %s on callback %s",
            command_name,
            callback_id,
        )
        return ExecuteCallbackCommandErrorResponse(
            error=f"Execution failed: {type(e).__name__}",
            error_type="execution_failed",
            callback_id=callback_id,
            command_name=command_name,
            source=source or None,
        )


async def core_list_callback_commands(
    ctx: Context, callback_id: int, source: str = ""
) -> ListCallbackCommandsResponse:
    """List commands loaded on a specific callback.

    Returns native agent commands plus any augment commands currently loaded on
    the callback. Use `source` to filter by the originating payload or service
    name (for example, `nano_bofs`). Use `callback_id` for all callback
    references; `display_id` is returned only for Mythic UI correlation.
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_callback_commands(mythic_ctx.mythic, callback_id, source)
    except (NoOperationSetError, CallbackNotFoundError, CommandError) as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_callback_commands")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_get_callback_command(
    ctx: Context, callback_id: int, command_name: str, source: str = ""
) -> GetCallbackCommandResponse:
    """Get rich metadata for one command loaded on a specific callback.

    Returns usage, description, attributes, and ordered parameter metadata for
    the loaded command, plus `argument_mode`, `execution_usage`,
    `example_arguments`, and `execution_notes` to clarify how `arguments`
    should be built. Use `source` to disambiguate commands that exist across
    multiple payload or service sources.
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_callback_command(
            mythic_ctx.mythic, callback_id, command_name, source
        )
    except (
        NoOperationSetError,
        CallbackNotFoundError,
        LoadedCommandNotFoundError,
        AmbiguousCommandError,
        CommandError,
    ) as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_callback_command")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_execute_callback_command(
    ctx: Context,
    callback_id: int,
    command_name: str,
    arguments: str = "",
    source: str = "",
    timeout: int = 60,
) -> ExecuteCallbackCommandSuccessResponse | ExecuteCallbackCommandErrorResponse:
    """Execute any command currently loaded on a callback.

    `arguments` is a string payload, not always raw CLI text. Some commands
    want raw command-line text while others want a JSON object string keyed by
    Mythic parameter names. Inspect `core_get_callback_command` for
    `argument_mode`, `execution_usage`, `example_arguments`, and
    `execution_notes` before tasking. Use `source` when the same command name
    exists across multiple payload or service sources.
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await execute_callback_command(
            mythic_ctx.mythic,
            callback_id,
            command_name,
            arguments,
            source,
            timeout,
        )
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_execute_callback_command")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))
