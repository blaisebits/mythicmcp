"""Operation tools for MythicMCP.

Provides tools for retrieving Mythic operation information:
- core_get_operation: Get current operation details and operator list
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    GetOperationResponse,
    ListOperationsResponse,
    OperationInfo,
    OperationSummary,
    OperatorInfo,
    SetOperationResponse,
)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


class OperationError(Exception):
    """Base exception for operation-related errors."""

    pass


class OperationNotFoundError(OperationError):
    """Raised when an operation is not found."""

    pass


class NoCurrentOperationError(OperationError):
    """Raised when no current operation is set."""

    pass


async def get_operation(
    mythic_instance: mythic_classes.Mythic,
    operation_id: Optional[int] = None,
) -> GetOperationResponse:
    """Fetch operation details from Mythic.

    Args:
        mythic_instance: Authenticated Mythic instance
        operation_id: Specific operation ID (defaults to current operation)

    Returns:
        GetOperationResponse with operation details and operators

    Raises:
        NoCurrentOperationError: If no current operation is set
        OperationNotFoundError: If specified operation is not found
        OperationError: For other operation-related errors
    """
    from mythic import mythic

    # Use current operation if not specified
    target_operation_id = operation_id or mythic_instance.current_operation_id

    if not target_operation_id:
        raise NoCurrentOperationError(
            "No current operation set. Configure an operation in Mythic UI."
        )

    # Query operation details
    operation_query = """
    query GetOperation($operation_id: Int!) {
        operation(where: {id: {_eq: $operation_id}}) {
            id
            name
            created_at
            complete
        }
    }
    """

    # Query operators for operation
    operators_query = """
    query GetOperators($operation_id: Int!) {
        operatoroperation(where: {operation_id: {_eq: $operation_id}}) {
            operator {
                username
                admin
                active
            }
        }
    }
    """

    try:
        # Fetch operation details
        operation_result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=operation_query,
            variables={"operation_id": target_operation_id},
        )

        operations = operation_result.get("operation", [])
        if not operations:
            raise OperationNotFoundError(
                f"Operation with ID {target_operation_id} not found"
            )

        operation_data = operations[0]

        # Parse created_at timestamp
        created_at_str = operation_data.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now()

        operation_info = OperationInfo(
            id=operation_data.get("id", 0),
            name=operation_data.get("name", ""),
            created_at=created_at,
            complete=operation_data.get("complete", False),
        )

        # Fetch operators
        operators_result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=operators_query,
            variables={"operation_id": target_operation_id},
        )

        operator_list = operators_result.get("operatoroperation", [])
        operators = []
        for op in operator_list:
            operator_data = op.get("operator", {})
            if operator_data.get("active", True):  # Only include active operators
                operators.append(
                    OperatorInfo(
                        username=operator_data.get("username", ""),
                        admin=operator_data.get("admin", False),
                    )
                )

        return GetOperationResponse(
            operation=operation_info,
            operators=operators,
        )

    except (OperationNotFoundError, NoCurrentOperationError):
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "permission" in error_msg or "access" in error_msg:
            raise OperationError(
                f"Access denied to operation {target_operation_id}"
            ) from e
        raise OperationError(
            f"Failed to retrieve operation: {type(e).__name__}"
        ) from e


async def list_operations(
    mythic_instance: mythic_classes.Mythic,
) -> ListOperationsResponse:
    """Fetch all operations the user has access to.

    Args:
        mythic_instance: Authenticated Mythic instance

    Returns:
        ListOperationsResponse with list of accessible operations

    Raises:
        OperationError: For operation-related errors
    """
    from mythic import mythic

    # Query all operations the user can see
    operations_query = """
    query GetOperations {
        operation(order_by: {name: asc}) {
            id
            name
            complete
            admin {
                username
            }
        }
    }
    """

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=operations_query,
            variables={},
        )

        operations_data = result.get("operation", [])
        operations = []

        for op in operations_data:
            admin_data = op.get("admin", {})
            operations.append(
                OperationSummary(
                    id=op.get("id", 0),
                    name=op.get("name", ""),
                    complete=op.get("complete", False),
                    admin_username=admin_data.get("username", "unknown"),
                )
            )

        return ListOperationsResponse(
            operations=operations,
            count=len(operations),
            current_operation_id=mythic_instance.current_operation_id,
        )

    except Exception as e:
        raise OperationError(
            f"Failed to list operations: {type(e).__name__}"
        ) from e


async def set_current_operation(
    mythic_instance: mythic_classes.Mythic,
    operation_id: int,
) -> SetOperationResponse:
    """Set the current operation for the authenticated user.

    Args:
        mythic_instance: Authenticated Mythic instance
        operation_id: The operation ID to set as current

    Returns:
        SetOperationResponse with result of the operation

    Raises:
        OperationNotFoundError: If operation doesn't exist or user lacks access
        OperationError: For other operation-related errors
    """
    import base64
    import json

    from mythic import mythic

    # Get user_id - try username first, then decode from API token
    user_id = None

    if mythic_instance.username:
        # Username/password auth - query for user ID
        get_user_id_query = """
        query getUserID($username: String!) {
            operator(where: {username: {_eq: $username}}) {
                id
            }
        }
        """
        try:
            user_result = await mythic.execute_custom_query(
                mythic=mythic_instance,
                query=get_user_id_query,
                variables={"username": mythic_instance.username},
            )
            operators = user_result.get("operator", [])
            if operators:
                user_id = operators[0].get("id")
        except Exception:
            pass

    if not user_id and mythic_instance.apitoken:
        # API token auth - decode JWT to get user_id
        try:
            # JWT format: header.payload.signature
            parts = mythic_instance.apitoken.split(".")
            if len(parts) >= 2:
                # Decode payload (add padding if needed)
                payload = parts[1]
                payload += "=" * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                jwt_data = json.loads(decoded)
                user_id = jwt_data.get("user_id")
        except Exception:
            pass

    if not user_id:
        raise OperationError("Cannot determine user ID from session or API token")

    # Use the updateCurrentOperation mutation
    set_operation_mutation = """
    mutation updateCurrentOperationMutation($user_id: Int!, $operation_id: Int!) {
        updateCurrentOperation(user_id: $user_id, operation_id: $operation_id) {
            status
            error
            operation_id
            name
        }
    }
    """

    try:

        # Now set the operation
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=set_operation_mutation,
            variables={"user_id": user_id, "operation_id": operation_id},
        )

        update_result = result.get("updateCurrentOperation", {})
        status = update_result.get("status", "")
        error = update_result.get("error", "")

        if status != "success":
            error_msg = error or f"Failed to set operation (status: {status})"
            raise OperationNotFoundError(error_msg)

        # Update the mythic instance's current operation
        mythic_instance.current_operation_id = operation_id

        return SetOperationResponse(
            success=True,
            operation_id=update_result.get("operation_id", operation_id),
            operation_name=update_result.get("name", ""),
            message=f"Successfully set current operation to '{update_result.get('name', '')}'",
        )

    except OperationNotFoundError:
        raise
    except OperationError:
        raise
    except Exception as e:
        raise OperationError(
            f"Failed to set operation: {type(e).__name__}"
        ) from e


async def core_list_operations(ctx: Context) -> ListOperationsResponse:
    """List all operations the authenticated user has access to.

    Returns operation names, IDs, completion status, and admin info.
    Use this to find available operations before setting one as current.
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_operations(mythic_ctx.mythic)
    except OperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_operations")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_set_operation(ctx: Context, operation_id: int) -> SetOperationResponse:
    """Set the current operation for this session.

    Changes the active operation context for all subsequent tool calls.
    Use core_list_operations first to find available operation IDs.

    Args:
        operation_id: The operation ID to set as current (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await set_current_operation(mythic_ctx.mythic, operation_id)
    except OperationNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except OperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_set_operation")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_get_operation(
    ctx: Context,
    operation_id: Optional[int] = None,
) -> GetOperationResponse:
    """Get information about the current Mythic operation.

    Returns operation name, creation date, and list of assigned operators.
    Use this to confirm the current operation context.

    Args:
        operation_id: Specific operation ID (optional, defaults to current operation)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_operation(mythic_ctx.mythic, operation_id)
    except NoCurrentOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except OperationNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except OperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_operation")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))
