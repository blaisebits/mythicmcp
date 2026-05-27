"""FastMCP server entry point for MythicMCP.

This module provides the main MCP server that exposes Mythic tools.
"""

from __future__ import annotations

import importlib
import logging
import sys
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context, FastMCP

from mythicmcp.config import get_startup_agents, is_dev_mode_enabled, is_hotload_enabled
from mythicmcp.connection import mythic_lifespan
from mythicmcp.models import (
    AgentToolsErrorResponse,
    AvailableAgentInfo,
    C2ProfileErrorResponse,
    CheckConnectionErrorResponse,
    CheckConnectionResponse,
    CreateC2InstanceResponse,
    CreatePayloadErrorResponse,
    CreatePayloadResponse,
    DeleteC2InstanceResponse,
    DeletePayloadErrorResponse,
    DeletePayloadResponse,
    DevReloadResponse,
    DownloadFileErrorResponse,
    DownloadFileResponse,
    DownloadPayloadErrorResponse,
    DownloadPayloadResponse,
    ExecuteCallbackCommandErrorResponse,
    ExecuteCallbackCommandSuccessResponse,
    GetC2InstanceResponse,
    GetC2ProfileParametersResponse,
    GetCallbackResponse,
    GetCallbackCommandResponse,
    GetFileBrowserByTaskResponse,
    GetInteractiveSessionResponse,
    GetOperationResponse,
    GetPayloadResponse,
    GetTaskCallbackResponse,
    GetTaskOutputResponse,
    ListCallbackCommandsResponse,
    ListAvailableAgentsResponse,
    ListC2InstancesResponse,
    ListC2ProfilesResponse,
    ListCallbackTasksResponse,
    ListFileBrowserResponse,
    ListInteractiveTasksResponse,
    ListCallbacksResponse,
    ListDownloadedFilesResponse,
    ListOperationsResponse,
    ListPayloadsResponse,
    ListPluginsResponse,
    ListUploadedFilesResponse,
    LoadAgentToolsResponse,
    PayloadConfigCheckResponse,
    PluginInfo,
    PluginLoadErrorInfo,
    SetOperationResponse,
    UnloadAgentToolsResponse,
    UploadFileErrorResponse,
    UploadFileResponse,
)

if TYPE_CHECKING:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastMCP server with Mythic lifespan
mcp = FastMCP(
    "MythicMCP",
    lifespan=mythic_lifespan,
)


USAGE_PATTERNS_RESOURCE = """Mythic MCP usage patterns

1. Set or confirm the current operation first with core_check_connection or core_set_operation.
2. Discover available commands on a callback with core_list_callback_commands.
3. Inspect one command with core_get_callback_command before executing it.
4. Execute with core_execute_callback_command.
5. After failures or timeouts, inspect task output before deciding why it failed.

Execution patterns:
- Treat `usage` as display/help text. When `usage` and `argument_mode` disagree, follow `argument_mode`.
- Zero-arg commands: use arguments: ""
- CLI-style commands: use raw text like whoami /all
- Structured augment or UI-backed commands: use a JSON object string keyed by parameter name, for example {"path":"C:\\\\Windows\\\\win.ini"}
- `execution_usage` is the exact MCP `arguments` payload to send when present.
- `example_arguments` is a starter payload that should usually match `execution_usage`.
- Use source when multiple payloads or services may expose the same command name
- Treat timeouts as ambiguous until task state and output are checked
- If core_execute_callback_command times out but returns a task ID, the task was still created. Inspect core_get_task_output next.
- If task-list status and task output disagree, trust task output. Status can lag behind the latest agent response.
"""


DEV_RELOAD_MODULES = (
    "mythicmcp.models",
    "mythicmcp.plugins.base",
    "mythicmcp.plugins.errors",
    "mythicmcp.plugins.registry",
    "mythicmcp.plugins.executor",
    "mythicmcp.plugins.yaml_loader",
    "mythicmcp.plugins",
)


def _reload_runtime_modules() -> list[str]:
    """Reload MythicMCP modules that are safe to refresh in-process."""
    importlib.invalidate_caches()

    module_names = [
        name for name in sorted(sys.modules)
        if name.startswith("mythicmcp.tools.")
    ]
    module_names.extend(
        name for name in DEV_RELOAD_MODULES if name in sys.modules
    )

    reloaded: list[str] = []
    for module_name in module_names:
        importlib.reload(sys.modules[module_name])
        reloaded.append(module_name)

    return reloaded


def reload_runtime(mcp_server: FastMCP | None = None) -> DevReloadResponse:
    """Reload Python tool modules and YAML plugins for local development."""
    reloaded_modules = _reload_runtime_modules()

    plugins_module = importlib.import_module("mythicmcp.plugins")
    reloaded_agents, reloaded_tool_count = plugins_module.reload_all_plugins(mcp_server)
    registry = plugins_module.get_registry()

    return DevReloadResponse(
        modules_reloaded=reloaded_modules,
        module_count=len(reloaded_modules),
        reloaded_agents=reloaded_agents,
        reloaded_tool_count=reloaded_tool_count,
        available_agents=len(registry.list_plugins()),
        plugin_load_errors=[
            PluginLoadErrorInfo(
                plugin_path=err.plugin_path,
                error=err.error_message,
            )
            for err in registry.get_load_errors()
        ],
    )


# --- Callback Tools (User Story 1 & 4) ---


@mcp.tool()
async def core_list_callbacks(ctx: Context) -> ListCallbacksResponse:
    """List all active callbacks (compromised hosts) in the current Mythic operation.

    Returns hostname, username, agent type, and other key details for each callback.
    Use this to get an overview of all active access in the engagement. Returned
    callback objects include canonical `callback_id` plus UI-only `display_id`.
    Use `callback_id` for all follow-on callback references.
    """
    from mythicmcp.tools.callbacks import core_list_callbacks as impl

    return await impl(ctx)


@mcp.tool()
async def core_get_callback(ctx: Context, callback_id: int) -> GetCallbackResponse:
    """Get detailed information about a specific Mythic callback by callback_id.

    Returns full callback configuration including host details, process info,
    integrity level, and agent configuration. Callbacks should be referenced
    by `callback_id`; `display_id` is returned only for Mythic UI correlation.

    Args:
        callback_id: Canonical callback_id to retrieve (required)
    """
    from mythicmcp.tools.callbacks import core_get_callback as impl

    return await impl(ctx, callback_id)


@mcp.tool()
async def core_list_callback_commands(
    ctx: Context, callback_id: int, source: str = ""
) -> ListCallbackCommandsResponse:
    """List all commands currently loaded on a specific callback.

    Requires a current Mythic operation. If you are in a fresh session, call
    `core_check_connection` or `core_set_operation` first.

    Returns native agent commands plus any augment commands that Mythic shows
    as loaded on the callback. Use `source` to filter by the originating
    payload or service name. Use `callback_id` for follow-on callback
    references; returned `display_id` values are UI-only correlation helpers.
    """
    from mythicmcp.tools.commands import core_list_callback_commands as impl

    return await impl(ctx, callback_id, source)


@mcp.tool()
async def core_get_callback_command(
    ctx: Context, callback_id: int, command_name: str, source: str = ""
) -> GetCallbackCommandResponse:
    """Get rich metadata for one command loaded on a specific callback.

    Requires a current Mythic operation. If you are in a fresh session, call
    `core_check_connection` or `core_set_operation` first.

    Returns usage, description, attributes, and ordered parameter metadata for
    the loaded command, plus `argument_mode`, `execution_usage`,
    `example_arguments`, and `execution_notes` to show how `arguments` should
    be built. `usage` is help/display text and may not match the exact
    execution payload format. For execution, prefer `execution_usage` and
    `argument_mode` over `usage`. Use `source` to disambiguate commands that
    originate from multiple payload or service sources.
    """
    from mythicmcp.tools.commands import core_get_callback_command as impl

    return await impl(ctx, callback_id, command_name, source)


@mcp.tool()
async def core_execute_callback_command(
    ctx: Context,
    callback_id: int,
    command_name: str,
    arguments: str = "",
    source: str = "",
    timeout: int = 60,
) -> ExecuteCallbackCommandSuccessResponse | ExecuteCallbackCommandErrorResponse:
    """Execute any command currently loaded on a callback.

    Requires a current Mythic operation. If you are in a fresh session, call
    `core_check_connection` or `core_set_operation` first.

    `arguments` is a string payload, not always raw CLI text. Some commands
    want raw command-line text while others want a JSON object string keyed by
    Mythic parameter names. Inspect `core_get_callback_command` for
    `argument_mode`, `execution_usage`, `example_arguments`, and
    `execution_notes` before tasking. For true zero-arg commands, use
    `arguments=""`. If the tool times out but returns `task_id` and
    `task_display_id`, the task was still created and should be inspected with
    `core_get_task_output`. Use `source` when the same command name exists
    across multiple payload or service sources.
    """
    from mythicmcp.tools.commands import core_execute_callback_command as impl

    return await impl(ctx, callback_id, command_name, arguments, source, timeout)


@mcp.resource("mythic://docs/usage-patterns")
def mythic_usage_patterns() -> str:
    """Short operator and agent guidance for common Mythic MCP command flows."""
    return USAGE_PATTERNS_RESOURCE


# --- Task Tools ---


@mcp.tool()
async def core_get_task_output(
    ctx: Context, task_display_id: int
) -> GetTaskOutputResponse:
    """Retrieve all output responses for a Mythic task by its display ID.

    Returns every output chunk Mythic has recorded for the task, in the order
    they were received. Useful for inspecting long-running or previously-issued
    tasks without re-executing them.

    Args:
        task_display_id: The task display ID to fetch output for (required)
    """
    from mythicmcp.tools.tasks import core_get_task_output as impl

    return await impl(ctx, task_display_id)


@mcp.tool()
async def core_list_callback_tasks(
    ctx: Context, callback_id: int
) -> ListCallbackTasksResponse:
    """List every task issued to a specific Mythic callback.

    Returns task metadata (command name, status, parameters, operator, timestamp)
    for every task recorded against the given callback. Use this to review what
    has already been run on a callback before issuing new work. Use
    `callback_id` for all callback references; returned `display_id` values are
    included only for Mythic UI correlation. Task `status` is a raw Mythic
    snapshot and can lag behind the latest task output.

    Args:
        callback_id: Canonical callback_id to list tasks for (required)
    """
    from mythicmcp.tools.tasks import core_list_callback_tasks as impl

    return await impl(ctx, callback_id)


@mcp.tool()
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
    from mythicmcp.tools.tasks import core_get_task_callback as impl

    return await impl(ctx, task_display_id)


# --- Interactive / PTY Session Tools ---


@mcp.tool()
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
    from mythicmcp.tools.tasks import core_list_interactive_tasks as impl

    return await impl(ctx, parent_task_display_id)


@mcp.tool()
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
    from mythicmcp.tools.tasks import core_get_interactive_session as impl

    return await impl(ctx, parent_task_display_id)


# --- File Browser Tools ---


@mcp.tool()
async def core_get_file_browser_by_task(
    ctx: Context, task_display_id: int
) -> GetFileBrowserByTaskResponse:
    """Retrieve file browser entries created by a specific Mythic task.

    Commands like poseidon_ls store their results in Mythic's file browser
    (filebrowserobj table) rather than as task response text. Use this tool
    to fetch the directory listing produced by such a task.

    Returns file/directory metadata: name, full path, size, permissions,
    access/modify times, and whether each entry is a file or directory.

    Args:
        task_display_id: The task display ID to fetch results for (required)
    """
    from mythicmcp.tools.filebrowser import core_get_file_browser_by_task as impl

    return await impl(ctx, task_display_id)


@mcp.tool()
async def core_list_file_browser(
    ctx: Context, host: str, path: str | None = None
) -> ListFileBrowserResponse:
    """List known file browser entries for a host across the current operation.

    Queries Mythic's accumulated file browser data for a given hostname.
    Optionally filter to entries whose parent path matches exactly (e.g.
    path="/etc" returns files directly inside /etc).

    This data is built up over time as agents run directory listing commands.
    It represents a composite view of everything Mythic has observed on that
    host, not just a single ls invocation.

    Args:
        host: Target hostname (required)
        path: Parent path to filter on (optional, e.g. "/etc")
    """
    from mythicmcp.tools.filebrowser import core_list_file_browser as impl

    return await impl(ctx, host, path)


# --- Operation Tools (User Story 2) ---


@mcp.tool()
async def core_list_operations(ctx: Context) -> ListOperationsResponse:
    """List all operations the authenticated user has access to.

    Returns operation names, IDs, completion status, and admin info.
    Use this to find available operations before setting one as current.
    """
    from mythicmcp.tools.operations import core_list_operations as impl

    return await impl(ctx)


@mcp.tool()
async def core_set_operation(ctx: Context, operation_id: int) -> SetOperationResponse:
    """Set the current operation for this session.

    Changes the active operation context for all subsequent tool calls.
    Use core_list_operations first to find available operation IDs.

    Args:
        operation_id: The operation ID to set as current (required)
    """
    from mythicmcp.tools.operations import core_set_operation as impl

    return await impl(ctx, operation_id)


@mcp.tool()
async def core_get_operation(
    ctx: Context,
    operation_id: int | None = None,
) -> GetOperationResponse:
    """Get information about the current Mythic operation.

    Returns operation name, creation date, and list of assigned operators.
    Use this to confirm the current operation context.

    Args:
        operation_id: Specific operation ID (optional, defaults to current operation)
    """
    from mythicmcp.tools.operations import core_get_operation as impl

    return await impl(ctx, operation_id)


# --- Status Tools (User Story 3) ---


@mcp.tool()
async def core_check_connection(
    ctx: Context,
) -> CheckConnectionResponse | CheckConnectionErrorResponse:
    """Verify connectivity and authentication status with the Mythic server.

    Use this tool to troubleshoot connection issues or confirm the server
    is reachable before performing operations.

    Returns connection status, authentication status, current operation name,
    and the operations accessible to the authenticated user. If connection
    fails, returns error details with the error type.
    """
    from mythicmcp.tools.status import core_check_connection as impl

    return await impl(ctx)


# --- Plugin Management Tools ---


@mcp.tool()
async def core_list_plugins(ctx: Context) -> ListPluginsResponse:
    """List all loaded agent plugins and their tools.

    Returns information about each loaded plugin including agent name,
    description, number of tools, and supported operating systems.
    Also reports any plugins that failed to load.

    Use this to see what agent-specific tools are available.
    """
    from mythicmcp.plugins import get_registry

    registry = get_registry()
    plugins = []

    for agent_name in registry.list_plugins():
        loaded = registry.get_loaded_plugin(agent_name)
        if loaded:
            plugins.append(
                PluginInfo(
                    agent_name=loaded.plugin.agent_name,
                    agent_description=loaded.plugin.agent_description,
                    tool_count=len(loaded.tools),
                    supported_os=loaded.plugin.supported_os,
                )
            )

    load_errors = [
        PluginLoadErrorInfo(plugin_path=err.plugin_path, error=err.error_message)
        for err in registry.get_load_errors()
    ]

    return ListPluginsResponse(
        plugins=plugins,
        total_count=len(plugins),
        load_errors=load_errors,
    )


# --- Dynamic Agent Loading Tools ---


if is_hotload_enabled():
    @mcp.tool()
    async def load_agent_tools(
        ctx: Context, agent_name: str
    ) -> LoadAgentToolsResponse | AgentToolsErrorResponse:
        """Dynamically load all tools for a specific agent into the MCP server.

        Agent tools are not loaded by default. Use this tool to activate an agent's
        tools when you need to interact with callbacks of that agent type.

        Use list_available_agents first to see what agents are available.

        After loading, the agent's tools will appear in the tool list (e.g.,
        apollo_shell, apollo_download, etc.).

        Args:
            agent_name: Agent identifier to load (e.g., "apollo", "poseidon", "arachne")
        """
        from mythicmcp.plugins import register_agent_with_mcp
        from mythicmcp.plugins.errors import AgentAlreadyLoadedError, AgentNotFoundError

        try:
            tool_names = register_agent_with_mcp(mcp, agent_name)
        except AgentAlreadyLoadedError as e:
            return AgentToolsErrorResponse(
                error=str(e),
                error_type="already_loaded",
                agent_name=agent_name,
            )
        except AgentNotFoundError as e:
            return AgentToolsErrorResponse(
                error=str(e),
                error_type="not_found",
                agent_name=agent_name,
            )

        # Notify client that tool list has changed
        try:
            await ctx.session.send_tool_list_changed()
        except Exception:
            logger.warning("Failed to send tools/list_changed notification")

        return LoadAgentToolsResponse(
            agent_name=agent_name,
            tools_loaded=len(tool_names),
            tool_names=tool_names,
        )


    @mcp.tool()
    async def unload_agent_tools(
        ctx: Context, agent_name: str
    ) -> UnloadAgentToolsResponse | AgentToolsErrorResponse:
        """Dynamically remove all tools for a specific agent from the MCP server.

        Use this to clean up the tool list when you no longer need a specific
        agent's tools. Core tools are not affected.

        Args:
            agent_name: Agent identifier to unload (e.g., "apollo", "poseidon", "arachne")
        """
        from mythicmcp.plugins import unregister_agent_from_mcp
        from mythicmcp.plugins.errors import AgentNotFoundError, AgentNotLoadedError

        try:
            removed_count = unregister_agent_from_mcp(mcp, agent_name)
        except AgentNotLoadedError as e:
            return AgentToolsErrorResponse(
                error=str(e),
                error_type="not_loaded",
                agent_name=agent_name,
            )
        except AgentNotFoundError as e:
            return AgentToolsErrorResponse(
                error=str(e),
                error_type="not_found",
                agent_name=agent_name,
            )

        # Notify client that tool list has changed
        try:
            await ctx.session.send_tool_list_changed()
        except Exception:
            logger.warning("Failed to send tools/list_changed notification")

        return UnloadAgentToolsResponse(
            agent_name=agent_name,
            tools_removed=removed_count,
        )


@mcp.tool()
async def list_available_agents(ctx: Context) -> ListAvailableAgentsResponse:
    """List all available agents and whether their tools are currently loaded.

    Shows every agent that was discovered at startup (from builtin plugins and
    external plugin directories), along with tool count, supported OS, and
    whether the agent's tools are currently active in the MCP server.

    Use load_agent_tools to activate an agent's tools.
    """
    from mythicmcp.plugins import get_registry

    registry = get_registry()
    agents = []

    for agent_name in registry.list_plugins():
        loaded = registry.get_loaded_plugin(agent_name)
        if loaded:
            agents.append(
                AvailableAgentInfo(
                    agent_name=loaded.plugin.agent_name,
                    agent_description=loaded.plugin.agent_description,
                    tool_count=len(loaded.tools),
                    supported_os=loaded.plugin.supported_os,
                    loaded=registry.is_agent_registered(agent_name),
                )
            )

    load_errors = [
        PluginLoadErrorInfo(plugin_path=err.plugin_path, error=err.error_message)
        for err in registry.get_load_errors()
    ]

    loaded_count = len(registry.list_registered_agents())

    return ListAvailableAgentsResponse(
        agents=agents,
        total_count=len(agents),
        loaded_count=loaded_count,
        load_errors=load_errors,
    )


if is_dev_mode_enabled():
    @mcp.tool()
    async def dev_reload_runtime(ctx: Context) -> DevReloadResponse:
        """Reload local MythicMCP code in-place for development.

        Picks up edits in core tool modules, plugin loader code, and YAML plugin
        definitions without restarting the MCP client. New top-level core tool
        schemas still require a one-time server restart.
        """
        response = reload_runtime(mcp)

        try:
            await ctx.session.send_tool_list_changed()
        except Exception:
            logger.warning("Failed to send tools/list_changed notification")

        return response


# --- C2 Profile Management Tools ---


@mcp.tool()
async def core_list_c2_profiles(
    ctx: Context,
) -> ListC2ProfilesResponse | C2ProfileErrorResponse:
    """List all available C2 profiles on the Mythic server.

    Returns each profile's name, description, type (P2P or server), and
    whether it is currently running. Use this to discover what C2 profiles
    are installed before querying their parameters or creating instances.
    """
    from mythicmcp.tools.c2profiles import core_list_c2_profiles as impl

    return await impl(ctx)


@mcp.tool()
async def core_get_c2_profile_parameters(
    ctx: Context, c2_profile_name: str
) -> GetC2ProfileParametersResponse | C2ProfileErrorResponse:
    """Get the parameter schema for a specific C2 profile.

    Returns every parameter the profile accepts: name, type, default value,
    whether it is required, valid choices for enum types, and description.
    Use this to understand what parameters are needed before creating a
    payload or saving a C2 instance.

    Args:
        c2_profile_name: Profile name (e.g., "http", "websocket", "tcp")
    """
    from mythicmcp.tools.c2profiles import core_get_c2_profile_parameters as impl

    return await impl(ctx, c2_profile_name)


@mcp.tool()
async def core_create_c2_instance(
    ctx: Context,
    instance_name: str,
    c2_profile_name: str,
    c2_parameters: str,
) -> CreateC2InstanceResponse | C2ProfileErrorResponse:
    """Save a named C2 profile configuration on the Mythic server.

    Creates a reusable, named set of C2 profile parameters that can be
    retrieved later with core_get_c2_instance and used when creating payloads.
    The instance is stored on the Mythic server, not locally.

    Use core_get_c2_profile_parameters first to see what parameters the
    profile expects.

    Args:
        instance_name: Name for this saved configuration (e.g., "http-staging")
        c2_profile_name: C2 profile type (e.g., "http", "websocket")
        c2_parameters: JSON object of parameter values (e.g., {"callback_host": "https://...", "callback_port": 443})
    """
    from mythicmcp.tools.c2profiles import core_create_c2_instance as impl

    return await impl(ctx, instance_name, c2_profile_name, c2_parameters)


@mcp.tool()
async def core_list_c2_instances(
    ctx: Context,
) -> ListC2InstancesResponse | C2ProfileErrorResponse:
    """List all saved C2 profile instances on the Mythic server.

    Returns the name and associated C2 profile type for each saved instance.
    Use core_get_c2_instance to retrieve the full parameter values.
    """
    from mythicmcp.tools.c2profiles import core_list_c2_instances as impl

    return await impl(ctx)


@mcp.tool()
async def core_get_c2_instance(
    ctx: Context, instance_name: str, c2_profile_name: str
) -> GetC2InstanceResponse | C2ProfileErrorResponse:
    """Get the full parameter values of a saved C2 profile instance.

    Returns the saved parameter values that can be used directly in
    core_create_payload's c2_profiles parameter.

    Args:
        instance_name: Name of the saved instance to retrieve
        c2_profile_name: C2 profile type (e.g., "http", "websocket")
    """
    from mythicmcp.tools.c2profiles import core_get_c2_instance as impl

    return await impl(ctx, instance_name, c2_profile_name)


@mcp.tool()
async def core_delete_c2_instance(
    ctx: Context, instance_name: str, c2_profile_name: str
) -> DeleteC2InstanceResponse | C2ProfileErrorResponse:
    """Delete a saved C2 profile instance from the Mythic server.

    Permanently removes the named instance. This cannot be undone.

    Args:
        instance_name: Name of the saved instance to delete
        c2_profile_name: C2 profile type (e.g., "http", "websocket")
    """
    from mythicmcp.tools.c2profiles import core_delete_c2_instance as impl

    return await impl(ctx, instance_name, c2_profile_name)


# --- File Management Tools ---


@mcp.tool()
async def core_upload_file(
    ctx: Context,
    filename: str = "",
    content: str = "",
    file_path: str = "",
) -> UploadFileResponse | UploadFileErrorResponse:
    """Upload a file to the Mythic server for use in agent tasking operations.

    The file will be stored on the Mythic server and can be used with agent
    upload commands (e.g., apollo_upload) by referencing the returned file_id.
    Provide either `content` or `file_path`, not both.

    Args:
        filename: Name for the file on Mythic server (optional when using file_path)
        content: Complete file as one valid base64 string, with no chunk markers, labels, or non-base64 text
        file_path: Local path to read and upload directly instead of supplying base64
    """
    from mythicmcp.tools.files import core_upload_file as impl

    return await impl(ctx, filename, content, file_path)


@mcp.tool()
async def core_download_file(
    ctx: Context,
    file_uuid: str,
) -> DownloadFileResponse | DownloadFileErrorResponse:
    """Download a file from the Mythic server by its UUID.

    Returns the file content as base64-encoded string along with metadata
    including filename, size, and hash values.

    Args:
        file_uuid: UUID of the file to download
    """
    from mythicmcp.tools.files import core_download_file as impl

    return await impl(ctx, file_uuid)


@mcp.tool()
async def core_list_downloaded_files(ctx: Context) -> ListDownloadedFilesResponse:
    """List all files downloaded from agents in the current operation.

    Returns file metadata including filename, source host, callback ID,
    and hash values for each file downloaded from target systems.
    """
    from mythicmcp.tools.files import core_list_downloaded_files as impl

    return await impl(ctx)


@mcp.tool()
async def core_list_uploaded_files(ctx: Context) -> ListUploadedFilesResponse:
    """List all files uploaded to the Mythic server in the current operation.

    Returns file metadata including file_id (for use in agent tasking),
    filename, upload timestamp, and operator who uploaded each file.
    """
    from mythicmcp.tools.files import core_list_uploaded_files as impl

    return await impl(ctx)


# --- Payload Tools ---


@mcp.tool()
async def core_list_payloads(ctx: Context) -> ListPayloadsResponse:
    """List all payloads in the current Mythic operation.

    Returns UUID, agent type, build status, OS, description, and C2 profiles
    for each payload. Includes auto-generated and deleted payloads with metadata flags.
    """
    from mythicmcp.tools.payloads import core_list_payloads as impl

    return await impl(ctx)


@mcp.tool()
async def core_get_payload(ctx: Context, payload_uuid: str) -> GetPayloadResponse:
    """Get detailed information about a specific Mythic payload by UUID.

    Returns build phase, build messages, operator, file metadata, C2 profile details,
    and other configuration for the specified payload.

    Args:
        payload_uuid: UUID of the payload to retrieve
    """
    from mythicmcp.tools.payloads import core_get_payload as impl

    return await impl(ctx, payload_uuid)


@mcp.tool()
async def core_create_payload(
    ctx: Context,
    payload_type_name: str,
    filename: str,
    operating_system: str,
    c2_profiles: str = "",
    c2_instances: str = "",
    description: str = "",
    commands: str = "",
    build_parameters: str = "",
    include_all_commands: bool = False,
    timeout: int = 300,
) -> CreatePayloadResponse | CreatePayloadErrorResponse:
    """Create and build a new standard payload on the Mythic server.

    Waits for the build to complete and returns the result. Wrapper payloads
    are not supported — use the Mythic UI for those.

    Args:
        payload_type_name: Agent type (e.g., "apollo", "poseidon")
        filename: Output filename for the payload
        operating_system: Target OS (e.g., "Windows", "Linux", "macOS")
        c2_profiles: JSON array of expanded C2 configs, e.g. [{"c2_profile": "http", "c2_profile_parameters": {"callback_host": "https://..."}}]
        c2_instances: JSON array of saved C2 instance references, e.g. [{"instance_name": "default"}]
        description: Payload description (optional)
        commands: JSON array of command names to include (optional)
        build_parameters: JSON array of build params [{"name": "...", "value": "..."}] (optional)
        include_all_commands: Include all commands for the agent type (optional, default false)
        timeout: Build timeout in seconds, 30-600 (optional, default 300)
    """
    from mythicmcp.tools.payloads import core_create_payload as impl

    return await impl(
        ctx, payload_type_name, filename, operating_system, c2_profiles,
        c2_instances, description, commands, build_parameters,
        include_all_commands, timeout,
    )


@mcp.tool()
async def core_download_payload(
    ctx: Context,
    payload_uuid: str,
) -> DownloadPayloadResponse | DownloadPayloadErrorResponse:
    """Download a built payload binary from the Mythic server by UUID.

    Returns the payload content as base64-encoded string along with filename
    and size metadata. The payload must have built successfully.

    Args:
        payload_uuid: UUID of the payload to download
    """
    from mythicmcp.tools.payloads import core_download_payload as impl

    return await impl(ctx, payload_uuid)


@mcp.tool()
async def core_delete_payload(
    ctx: Context,
    payload_uuid: str,
) -> DeletePayloadResponse | DeletePayloadErrorResponse:
    """Soft-delete a payload from the current Mythic operation.

    Marks the payload as deleted. This is reversible through the Mythic UI.

    Args:
        payload_uuid: UUID of the payload to delete
    """
    from mythicmcp.tools.payloads import core_delete_payload as impl

    return await impl(ctx, payload_uuid)


@mcp.tool()
async def core_check_payload_config(
    ctx: Context,
    payload_uuid: str,
) -> PayloadConfigCheckResponse:
    """Validate a payload's C2 configuration against running C2 profiles.

    Checks whether the payload's C2 settings are compatible with the active
    C2 profile configuration on the Mythic server.

    Args:
        payload_uuid: UUID of the payload to check
    """
    from mythicmcp.tools.payloads import core_check_payload_config as impl

    return await impl(ctx, payload_uuid)


@mcp.tool()
async def core_payload_redirect_rules(
    ctx: Context,
    payload_uuid: str,
) -> PayloadConfigCheckResponse:
    """Get redirect rules for a payload's C2 configuration.

    Returns the redirect/redirector rules that should be configured for the
    payload's C2 profile to properly route traffic.

    Args:
        payload_uuid: UUID of the payload to get rules for
    """
    from mythicmcp.tools.payloads import core_payload_redirect_rules as impl

    return await impl(ctx, payload_uuid)


CONFIGURATION_GUIDANCE = """
MythicMCP Configuration Required
================================

MythicMCP needs connection credentials for your Mythic server.

Option 1: API Token (Recommended)
---------------------------------
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_API_TOKEN="your-api-token-here"

Option 2: Username/Password
---------------------------
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_USERNAME="mythic_admin"
export MYTHIC_PASSWORD="your-password-here"

For MCP client configuration (Claude Desktop, Cursor, etc.), add
environment variables to your MCP server configuration file.

See: https://github.com/blaisebits/mythicmcp#configuration
"""


def _load_plugins() -> None:
    """Load all plugins into the registry (without registering tools with MCP).

    Agent tools may be auto-registered at startup via MYTHIC_AGENTS.
    """
    from mythicmcp.plugins import load_all_plugins, register_agent_with_mcp
    from mythicmcp.plugins.errors import AgentAlreadyLoadedError, AgentNotFoundError

    logger.info("Loading plugins...")
    registry = load_all_plugins()
    logger.info(
        f"Loaded {len(registry.list_plugins())} plugins into registry"
    )

    startup_agents = get_startup_agents()
    if not startup_agents:
        return
    if startup_agents == ["all"]:
        startup_agents = registry.list_plugins()

    for agent_name in startup_agents:
        try:
            tool_names = register_agent_with_mcp(mcp, agent_name)
            logger.info(
                "Preloaded %s tools for agent '%s' from MYTHIC_AGENTS",
                len(tool_names),
                agent_name,
            )
        except AgentAlreadyLoadedError:
            logger.info("Agent '%s' was already preloaded", agent_name)
        except AgentNotFoundError:
            logger.warning(
                "Skipping unknown startup agent '%s' from MYTHIC_AGENTS",
                agent_name,
            )


def main() -> None:
    """Run the MythicMCP server."""
    import sys

    from mythicmcp.config import ConfigurationError
    from mythicmcp.connection import MythicAuthenticationError, MythicConnectionError

    logger.info("Starting MythicMCP server...")

    # Load plugins before starting server
    _load_plugins()

    try:
        mcp.run()
    except (ConfigurationError, MythicAuthenticationError, MythicConnectionError) as e:
        # Print user-friendly guidance instead of stack trace
        print(f"\nError: {e}\n", file=sys.stderr)
        print(CONFIGURATION_GUIDANCE, file=sys.stderr)
        sys.exit(1)
    except ExceptionGroup as eg:
        # FastMCP wraps errors in ExceptionGroup - extract and handle
        for exc in eg.exceptions:
            if isinstance(exc, (ConfigurationError, MythicAuthenticationError, MythicConnectionError)):
                print(f"\nError: {exc}\n", file=sys.stderr)
                print(CONFIGURATION_GUIDANCE, file=sys.stderr)
                sys.exit(1)
        # Re-raise if not a configuration error
        raise


if __name__ == "__main__":
    main()
