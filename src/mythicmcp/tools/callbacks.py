"""Callback tools for MythicMCP.

Provides tools for listing and retrieving Mythic callbacks:
- core_list_callbacks: List all active callbacks in the current operation
- core_get_callback: Get detailed information about a specific callback
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    CallbackDetail,
    CallbackSummary,
    GetCallbackResponse,
    ListCallbacksResponse,
)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


class CallbackError(Exception):
    """Base exception for callback operations."""

    pass


class CallbackNotFoundError(CallbackError):
    """Raised when a callback is not found."""

    pass


class NoOperationSetError(CallbackError):
    """Raised when no current operation is set in Mythic."""

    pass


def _parse_callback_summary(callback_data: dict) -> CallbackSummary:
    """Parse raw callback data from Mythic into CallbackSummary model.

    Args:
        callback_data: Raw callback data from GraphQL response

    Returns:
        CallbackSummary model
    """
    # Extract agent type from nested payload structure
    agent_type = ""
    if payload := callback_data.get("payload"):
        if payloadtype := payload.get("payloadtype"):
            agent_type = payloadtype.get("name", "")

    return CallbackSummary(
        id=callback_data.get("id", 0),
        display_id=callback_data.get("display_id", 0),
        hostname=callback_data.get("host", ""),
        username=callback_data.get("user", ""),
        agent_type=agent_type,
        os=callback_data.get("os", ""),
        internal_ip=callback_data.get("ip", ""),
        integrity_level=callback_data.get("integrity_level", 0),
        process_name=callback_data.get("process_name", ""),
        active=callback_data.get("active", True),
    )


def _parse_callback_detail(callback_data: dict) -> CallbackDetail:
    """Parse raw callback data from Mythic into CallbackDetail model.

    Args:
        callback_data: Raw callback data from GraphQL response

    Returns:
        CallbackDetail model
    """
    # Extract agent type from nested payload structure
    agent_type = ""
    if payload := callback_data.get("payload"):
        if payloadtype := payload.get("payloadtype"):
            agent_type = payloadtype.get("name", "")

    return CallbackDetail(
        id=callback_data.get("id", 0),
        display_id=callback_data.get("display_id", 0),
        hostname=callback_data.get("host", ""),
        username=callback_data.get("user", ""),
        domain=callback_data.get("domain", ""),
        internal_ip=callback_data.get("ip", ""),
        external_ip=callback_data.get("external_ip", ""),
        os=callback_data.get("os", ""),
        architecture=callback_data.get("architecture", ""),
        process_id=callback_data.get("pid", 0),
        process_name=callback_data.get("process_name", ""),
        integrity_level=callback_data.get("integrity_level", 0),
        agent_type=agent_type,
        description=callback_data.get("description", ""),
        active=callback_data.get("active", True),
    )


async def list_callbacks(mythic_instance: mythic_classes.Mythic) -> ListCallbacksResponse:
    """Fetch all active callbacks from Mythic.

    Args:
        mythic_instance: Authenticated Mythic instance

    Returns:
        ListCallbacksResponse with callbacks list

    Raises:
        NoOperationSetError: If no current operation is set
        CallbackError: For other callback-related errors
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Configure an operation in Mythic UI."
        )

    try:
        callbacks_data = await mythic.get_all_active_callbacks(mythic_instance)

        callbacks = [_parse_callback_summary(cb) for cb in callbacks_data]

        return ListCallbacksResponse(
            callbacks=callbacks,
            count=len(callbacks),
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Configure an operation in Mythic UI."
            ) from e
        raise CallbackError(f"Failed to retrieve callbacks: {type(e).__name__}") from e


async def get_callback_by_id(
    mythic_instance: mythic_classes.Mythic, callback_id: int
) -> GetCallbackResponse:
    """Fetch a specific callback by ID from Mythic.

    Args:
        mythic_instance: Authenticated Mythic instance
        callback_id: The callback ID to retrieve

    Returns:
        GetCallbackResponse with callback details

    Raises:
        CallbackNotFoundError: If callback does not exist
        NoOperationSetError: If no current operation is set
        CallbackError: For other callback-related errors
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Configure an operation in Mythic UI."
        )

    if callback_id <= 0:
        raise CallbackNotFoundError(f"Invalid callback ID: {callback_id}")

    # Use custom GraphQL query to fetch single callback
    query = """
    query GetCallbackById($callback_id: Int!) {
        callback(where: {id: {_eq: $callback_id}}) {
            id
            display_id
            host
            user
            domain
            ip
            external_ip
            os
            architecture
            pid
            process_name
            integrity_level
            description
            active
            payload {
                payloadtype {
                    name
                }
            }
        }
    }
    """

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=query,
            variables={"callback_id": callback_id},
        )

        callbacks = result.get("callback", [])
        if not callbacks:
            raise CallbackNotFoundError(f"Callback with ID {callback_id} not found")

        callback_data = callbacks[0]

        # Check if callback belongs to current operation (access control)
        # The GraphQL query already filters by operation context

        return GetCallbackResponse(
            callback=_parse_callback_detail(callback_data),
        )

    except CallbackNotFoundError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "permission" in error_msg or "access" in error_msg or "denied" in error_msg:
            raise CallbackError(f"Access denied to callback {callback_id}") from e
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Configure an operation in Mythic UI."
            ) from e
        raise CallbackError(
            f"Failed to retrieve callback {callback_id}: {type(e).__name__}"
        ) from e


# Tool registration functions - these will be decorated in server.py


async def core_list_callbacks(ctx: Context) -> ListCallbacksResponse:
    """List all active callbacks (compromised hosts) in the current Mythic operation.

    Returns hostname, username, agent type, and other key details for each callback.
    Use this to get an overview of all active access in the engagement.
    """
    from mcp.server.fastmcp import ToolError

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_callbacks(mythic_ctx.mythic)
    except NoOperationSetError as e:
        raise ToolError(str(e))
    except CallbackError as e:
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in core_list_callbacks")
        raise ToolError(f"Unexpected error: {type(e).__name__}")


async def core_get_callback(ctx: Context, callback_id: int) -> GetCallbackResponse:
    """Get detailed information about a specific Mythic callback by ID.

    Returns full callback configuration including host details, process info,
    integrity level, and agent configuration.

    Args:
        callback_id: The callback ID to retrieve (required)
    """
    from mcp.server.fastmcp import ToolError

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_callback_by_id(mythic_ctx.mythic, callback_id)
    except CallbackNotFoundError as e:
        raise ToolError(str(e))
    except NoOperationSetError as e:
        raise ToolError(str(e))
    except CallbackError as e:
        raise ToolError(str(e))
    except Exception as e:
        logger.exception("Unexpected error in core_get_callback")
        raise ToolError(f"Unexpected error: {type(e).__name__}")
