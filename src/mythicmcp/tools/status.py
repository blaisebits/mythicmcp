"""Status tools for MythicMCP.

Provides tools for checking Mythic server connectivity:
- core_check_connection: Verify connectivity and authentication status
"""

from __future__ import annotations

import json
import logging
from base64 import b64decode
from typing import TYPE_CHECKING, Union

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    CheckConnectionErrorResponse,
    CheckConnectionResponse,
)

if TYPE_CHECKING:
    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


def _extract_user_id_from_token(token: str | None) -> int | None:
    """Extract user_id from a Mythic API token JWT payload."""
    if not token:
        return None
    try:
        payload_b64 = token.split(".")[1]
        # Add padding for base64
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(b64decode(payload_b64))
        return payload.get("user_id")
    except Exception:
        return None


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
    from mythicmcp.tools.operations import list_operations

    try:
        mythic_instance = mythic_ctx.mythic
        config = mythic_ctx.config

        # Extract user_id from API token JWT to query the right operator
        user_id = _extract_user_id_from_token(mythic_instance.apitoken)

        # Query operator record — verifies connectivity, auth, and gets current op
        whoami_query = """
        query whoami($user_id: Int!) {
            operator(where: {id: {_eq: $user_id}}) {
                username
                current_operation_id
            }
        }
        """
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=whoami_query,
            variables={"user_id": user_id} if user_id else {},
        )

        # If no user_id from token, fall back to first operator
        if not user_id:
            whoami_query = """
            query whoami {
                operator(limit: 1) {
                    username
                    current_operation_id
                }
            }
            """
            result = await mythic.execute_custom_query(
                mythic=mythic_instance,
                query=whoami_query,
            )

        operators = result.get("operator", [])

        # Auto-set operation if not already set and user has one
        current_operation_name = None
        if operators:
            user_op_id = operators[0].get("current_operation_id")
            if user_op_id and not mythic_instance.current_operation_id:
                mythic_instance.current_operation_id = user_op_id
                logger.info(f"Auto-set operation to ID {user_op_id} from user profile")

        # Resolve operation name
        op_id = mythic_instance.current_operation_id
        if op_id:
            try:
                operation_query = """
                query GetCurrentOperation($operation_id: Int!) {
                    operation(where: {id: {_eq: $operation_id}}) {
                        name
                    }
                }
                """
                op_result = await mythic.execute_custom_query(
                    mythic=mythic_instance,
                    query=operation_query,
                    variables={"operation_id": op_id},
                )
                op_list = op_result.get("operation", [])
                if op_list:
                    current_operation_name = op_list[0].get("name")
            except Exception:
                pass

        accessible_operations = []
        try:
            operations_response = await list_operations(mythic_instance)
            accessible_operations = operations_response.operations
        except Exception:
            logger.warning("Failed to list accessible operations during connection check")

        return CheckConnectionResponse(
            connected=True,
            server_url=config.safe_server_url,
            authenticated=True,
            current_operation=current_operation_name,
            accessible_operations=accessible_operations,
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
    Also returns the operations accessible to the authenticated user so callers
    can prompt for or switch operations. If connection fails, returns error
    details with the error type.
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    return await check_connection(mythic_ctx)
