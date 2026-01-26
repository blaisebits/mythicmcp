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
    OperationInfo,
    OperatorInfo,
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
    from mcp.server.fastmcp import ToolError

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_operation(mythic_ctx.mythic, operation_id)
    except NoCurrentOperationError as e:
        raise ToolError(str(e))
    except OperationNotFoundError as e:
        raise ToolError(str(e))
    except OperationError as e:
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in core_get_operation")
        raise ToolError(f"Unexpected error: {type(e).__name__}")
