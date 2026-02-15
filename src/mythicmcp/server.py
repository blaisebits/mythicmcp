"""FastMCP server entry point for MythicMCP.

This module provides the main MCP server that exposes Mythic tools.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context, FastMCP

from mythicmcp.connection import mythic_lifespan
from mythicmcp.models import (
    CheckConnectionErrorResponse,
    CheckConnectionResponse,
    DownloadFileErrorResponse,
    DownloadFileResponse,
    GetCallbackResponse,
    GetOperationResponse,
    ListCallbacksResponse,
    ListDownloadedFilesResponse,
    ListOperationsResponse,
    ListPluginsResponse,
    ListUploadedFilesResponse,
    PluginInfo,
    PluginLoadErrorInfo,
    SetOperationResponse,
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


# --- Callback Tools (User Story 1 & 4) ---


@mcp.tool()
async def core_list_callbacks(ctx: Context) -> ListCallbacksResponse:
    """List all active callbacks (compromised hosts) in the current Mythic operation.

    Returns hostname, username, agent type, and other key details for each callback.
    Use this to get an overview of all active access in the engagement.
    """
    from mythicmcp.tools.callbacks import core_list_callbacks as impl

    return await impl(ctx)


@mcp.tool()
async def core_get_callback(ctx: Context, callback_id: int) -> GetCallbackResponse:
    """Get detailed information about a specific Mythic callback by ID.

    Returns full callback configuration including host details, process info,
    integrity level, and agent configuration.

    Args:
        callback_id: The callback ID to retrieve (required)
    """
    from mythicmcp.tools.callbacks import core_get_callback as impl

    return await impl(ctx, callback_id)


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

    Returns connection status, authentication status, and current operation name.
    If connection fails, returns error details with the error type.
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


# --- File Management Tools ---


@mcp.tool()
async def core_upload_file(
    ctx: Context,
    filename: str,
    content: str,
) -> UploadFileResponse | UploadFileErrorResponse:
    """Upload a file to the Mythic server for use in agent tasking operations.

    The file will be stored on the Mythic server and can be used with agent
    upload commands (e.g., apollo_upload) by referencing the returned file_id.

    Args:
        filename: Name for the file on Mythic server
        content: Base64-encoded file content
    """
    from mythicmcp.tools.files import core_upload_file as impl

    return await impl(ctx, filename, content)


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

See: https://github.com/user/mythicmcp#configuration
"""


def _load_plugins() -> None:
    """Load and register all plugins with the MCP server."""
    from mythicmcp.plugins import load_all_plugins, register_plugin_tools

    logger.info("Loading plugins...")
    registry = load_all_plugins()
    logger.info(f"Loaded {len(registry.list_plugins())} plugins")

    register_plugin_tools(mcp)


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
