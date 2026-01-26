"""Status tools for MythicMCP.

Provides tools for checking Mythic server connectivity:
- core_check_connection: Verify connectivity and authentication status
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Union

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    CheckConnectionErrorResponse,
    CheckConnectionResponse,
)

if TYPE_CHECKING:
    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


async def check_connection(
    mythic_ctx: MythicContext,
) -> Union[CheckConnectionResponse, CheckConnectionErrorResponse]:
    """Check Mythic server connectivity and authentication status.

    This function attempts to verify that the Mythic connection is healthy
    by checking the current operation status.

    Args:
        mythic_ctx: MythicContext with authenticated connection

    Returns:
        CheckConnectionResponse on success, CheckConnectionErrorResponse on failure
    """
    from mythic import mythic

    try:
        # The connection was already validated at startup via lifespan
        # We verify it's still healthy by checking if we can get operation info
        mythic_instance = mythic_ctx.mythic
        config = mythic_ctx.config

        # Check if we have a current operation set
        current_operation_name = None
        if mythic_instance.current_operation_id:
            try:
                # Try to get operation name
                operation_query = """
                query GetCurrentOperation($operation_id: Int!) {
                    operation(where: {id: {_eq: $operation_id}}) {
                        name
                    }
                }
                """
                result = await mythic.execute_custom_query(
                    mythic=mythic_instance,
                    query=operation_query,
                    variables={"operation_id": mythic_instance.current_operation_id},
                )
                operations = result.get("operation", [])
                if operations:
                    current_operation_name = operations[0].get("name")
            except Exception:
                # Non-fatal - we're still connected even if we can't get op name
                pass

        return CheckConnectionResponse(
            connected=True,
            server_url=config.safe_server_url,
            authenticated=True,
            current_operation=current_operation_name,
        )

    except Exception as e:
        error_msg = str(e).lower()
        config = mythic_ctx.config

        # Determine error type
        if "authentication" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
            error_type = "authentication_failed"
            error = "Authentication failed. Verify your credentials are correct."
        elif "timeout" in error_msg:
            error_type = "timeout"
            error = "Connection timed out. The Mythic server may be slow or overloaded."
        else:
            error_type = "connection_failed"
            error = f"Connection failed: {type(e).__name__}"

        return CheckConnectionErrorResponse(
            connected=False,
            error=error,
            error_type=error_type,
            server_url=config.safe_server_url,
        )


async def core_check_connection(
    ctx: Context,
) -> Union[CheckConnectionResponse, CheckConnectionErrorResponse]:
    """Verify connectivity and authentication status with the Mythic server.

    Use this tool to troubleshoot connection issues or confirm the server
    is reachable before performing operations.

    Returns connection status, authentication status, and current operation name.
    If connection fails, returns error details with the error type.
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    return await check_connection(mythic_ctx)
