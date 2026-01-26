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
    GetCallbackResponse,
    GetOperationResponse,
    ListCallbacksResponse,
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


def main() -> None:
    """Run the MythicMCP server."""
    import sys

    from mythicmcp.config import ConfigurationError
    from mythicmcp.connection import MythicAuthenticationError, MythicConnectionError

    logger.info("Starting MythicMCP server...")

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
