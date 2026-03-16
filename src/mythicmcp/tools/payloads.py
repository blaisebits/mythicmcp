"""Payload management tools for MythicMCP.

Provides tools for managing Mythic payloads:
- core_list_payloads: List all payloads in the current operation
- core_get_payload: Get detailed payload information by UUID
- core_create_payload: Create and build a new standard payload
- core_download_payload: Download a built payload binary
- core_check_payload_config: Validate payload C2 configuration
- core_payload_redirect_rules: Get redirect rules for a payload
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    C2ProfileSummary,
    CreatePayloadErrorResponse,
    CreatePayloadResponse,
    DeletePayloadErrorResponse,
    DeletePayloadResponse,
    DownloadPayloadErrorResponse,
    DownloadPayloadResponse,
    GetPayloadResponse,
    ListPayloadsResponse,
    PayloadConfigCheckResponse,
    PayloadDetail,
    PayloadSummary,
)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


# --- Exception Classes ---


class PayloadError(Exception):
    """Base exception for payload operations."""

    pass


class PayloadNotFoundError(PayloadError):
    """Raised when a payload is not found by UUID."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        super().__init__(f"Payload with UUID {uuid} not found")


class NoOperationError(PayloadError):
    """Raised when no current operation is set."""

    def __init__(self):
        super().__init__("No current operation set. Use core_set_operation first.")


class PayloadBuildError(PayloadError):
    """Raised when payload build fails."""

    def __init__(self, uuid: str, message: str):
        self.uuid = uuid
        self.message = message
        super().__init__(f"Payload build failed ({uuid}): {message}")


class PayloadDownloadError(PayloadError):
    """Raised when payload download fails."""

    def __init__(self, uuid: str, reason: str):
        self.uuid = uuid
        self.reason = reason
        super().__init__(f"Cannot download payload {uuid}: {reason}")


class InvalidJSONError(PayloadError):
    """Raised when JSON input is malformed."""

    def __init__(self, param_name: str, details: str):
        self.param_name = param_name
        super().__init__(f"Invalid JSON for '{param_name}': {details}")


class ConnectionError(PayloadError):
    """Raised when connection to Mythic server fails."""

    def __init__(self, details: str):
        self.details = details
        super().__init__(f"Failed to connect to Mythic server: {details}")


# --- Helper Functions ---


def _parse_c2_profile_summary(c2_data: dict) -> C2ProfileSummary:
    """Parse nested C2 profile data from GraphQL response."""
    profile = c2_data.get("c2profile", {})
    return C2ProfileSummary(
        name=profile.get("name", ""),
        is_p2p=profile.get("is_p2p", False),
        running=profile.get("running", False),
    )


def _parse_payload_summary(payload_data: dict) -> PayloadSummary:
    """Parse raw payload data into PayloadSummary model."""
    agent_type = ""
    if payloadtype := payload_data.get("payloadtype"):
        agent_type = payloadtype.get("name", "")

    c2_profiles = [
        _parse_c2_profile_summary(c2)
        for c2 in payload_data.get("payloadc2profiles", [])
    ]

    creation_time_str = payload_data.get("creation_time", "")
    try:
        creation_time = datetime.fromisoformat(creation_time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        creation_time = datetime.now(timezone.utc)

    return PayloadSummary(
        uuid=payload_data.get("uuid", ""),
        agent_type=agent_type,
        build_phase=payload_data.get("build_phase", ""),
        description=payload_data.get("description", "") or "",
        deleted=payload_data.get("deleted", False),
        auto_generated=payload_data.get("auto_generated", False),
        creation_time=creation_time,
        os=payload_data.get("os", "") or "",
        c2_profiles=c2_profiles,
    )


def _parse_payload_detail(payload_data: dict) -> PayloadDetail:
    """Parse raw payload data into PayloadDetail model."""
    agent_type = ""
    if payloadtype := payload_data.get("payloadtype"):
        agent_type = payloadtype.get("name", "")

    c2_profiles = [
        _parse_c2_profile_summary(c2)
        for c2 in payload_data.get("payloadc2profiles", [])
    ]

    operator = ""
    if operator_data := payload_data.get("operator"):
        operator = operator_data.get("username", "") or ""

    file_uuid = None
    filename = None
    if filemetum := payload_data.get("filemetum"):
        file_uuid = filemetum.get("agent_file_id")
        filename = filemetum.get("filename_utf8")

    creation_time_str = payload_data.get("creation_time", "")
    try:
        creation_time = datetime.fromisoformat(creation_time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        creation_time = datetime.now(timezone.utc)

    return PayloadDetail(
        uuid=payload_data.get("uuid", ""),
        agent_type=agent_type,
        build_phase=payload_data.get("build_phase", ""),
        build_message=payload_data.get("build_message", "") or "",
        build_stderr=payload_data.get("build_stderr", "") or "",
        callback_alert=payload_data.get("callback_alert", False),
        description=payload_data.get("description", "") or "",
        deleted=payload_data.get("deleted", False),
        auto_generated=payload_data.get("auto_generated", False),
        creation_time=creation_time,
        operator=operator,
        file_uuid=file_uuid,
        filename=filename,
        os=payload_data.get("os", "") or "",
        c2_profiles=c2_profiles,
    )


def _parse_c2_profiles_json(json_str: str) -> list[dict]:
    """Parse and validate C2 profiles JSON string."""
    if not json_str or not json_str.strip():
        raise InvalidJSONError("c2_profiles", "C2 profiles are required and cannot be empty")

    try:
        profiles = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise InvalidJSONError("c2_profiles", str(e))

    if not isinstance(profiles, list):
        raise InvalidJSONError("c2_profiles", "Must be a JSON array")

    for i, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise InvalidJSONError("c2_profiles", f"Item {i} must be an object")
        if "c2_profile" not in profile:
            raise InvalidJSONError("c2_profiles", f"Item {i} missing 'c2_profile' key")
        if "c2_profile_parameters" not in profile or not isinstance(
            profile["c2_profile_parameters"], dict
        ):
            raise InvalidJSONError(
                "c2_profiles", f"Item {i} missing or invalid 'c2_profile_parameters' dict"
            )

    return profiles


def _parse_build_parameters_json(json_str: str) -> list[dict]:
    """Parse and validate build parameters JSON string."""
    if not json_str or not json_str.strip():
        return []

    try:
        params = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise InvalidJSONError("build_parameters", str(e))

    if not isinstance(params, list):
        raise InvalidJSONError("build_parameters", "Must be a JSON array")

    for i, param in enumerate(params):
        if not isinstance(param, dict):
            raise InvalidJSONError("build_parameters", f"Item {i} must be an object")
        if "name" not in param or "value" not in param:
            raise InvalidJSONError("build_parameters", f"Item {i} missing 'name' or 'value' key")

    return params


def _parse_commands_json(json_str: str) -> list[str]:
    """Parse and validate commands JSON string."""
    if not json_str or not json_str.strip():
        return []

    try:
        commands = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise InvalidJSONError("commands", str(e))

    if not isinstance(commands, list):
        raise InvalidJSONError("commands", "Must be a JSON array of strings")

    for i, cmd in enumerate(commands):
        if not isinstance(cmd, str):
            raise InvalidJSONError("commands", f"Item {i} must be a string")

    return commands


# --- Custom GraphQL attributes for list view ---

LIST_PAYLOADS_ATTRIBUTES = """
uuid
build_phase
description
deleted
auto_generated
creation_time
os
payloadtype {
    name
}
payloadc2profiles {
    c2profile {
        name
        running
        is_p2p
    }
}
"""


# --- Business Logic Functions ---


async def list_payloads(
    mythic_instance: mythic_classes.Mythic,
) -> ListPayloadsResponse:
    """Fetch all payloads in the current operation."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    try:
        payloads_data = await mythic.get_all_payloads(
            mythic=mythic_instance,
            custom_return_attributes=LIST_PAYLOADS_ATTRIBUTES,
        )

        payloads = [_parse_payload_summary(p) for p in payloads_data]

        return ListPayloadsResponse(
            payloads=payloads,
            count=len(payloads),
        )

    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        if "operation" in error_msg:
            raise NoOperationError()
        raise ConnectionError(f"Failed to list payloads: {e}")


async def get_payload_by_uuid(
    mythic_instance: mythic_classes.Mythic,
    payload_uuid: str,
) -> GetPayloadResponse:
    """Fetch detailed payload information by UUID."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not payload_uuid or not payload_uuid.strip():
        raise PayloadNotFoundError(payload_uuid)

    try:
        payload_data = await mythic.get_payload_by_uuid(
            mythic=mythic_instance,
            payload_uuid=payload_uuid,
        )

        return GetPayloadResponse(
            payload=_parse_payload_detail(payload_data),
        )

    except PayloadNotFoundError:
        raise
    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "failed to find" in error_msg:
            raise PayloadNotFoundError(payload_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        if "operation" in error_msg:
            raise NoOperationError()
        raise PayloadNotFoundError(payload_uuid)


async def create_payload(
    mythic_instance: mythic_classes.Mythic,
    payload_type_name: str,
    filename: str,
    operating_system: str,
    c2_profiles: list[dict],
    commands: list[str] | None = None,
    build_parameters: list[dict] | None = None,
    description: str = "",
    include_all_commands: bool = False,
    timeout: int = 300,
) -> CreatePayloadResponse:
    """Create and build a new standard payload on Mythic."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    try:
        result = await mythic.create_payload(
            mythic=mythic_instance,
            payload_type_name=payload_type_name,
            filename=filename,
            operating_system=operating_system,
            c2_profiles=c2_profiles,
            commands=commands,
            build_parameters=build_parameters,
            description=description,
            return_on_complete=True,
            timeout=timeout,
            include_all_commands=include_all_commands,
        )

        uuid = result.get("uuid", "")
        build_phase = result.get("build_phase", "")
        build_message = result.get("build_message", "") or ""

        if build_phase != "success":
            build_stderr = result.get("build_stderr", "") or ""
            msg = build_message
            if build_stderr:
                msg = f"{build_message}. stderr: {build_stderr}"
            raise PayloadBuildError(uuid, msg)

        return CreatePayloadResponse(
            uuid=uuid,
            build_phase=build_phase,
            build_message=build_message,
        )

    except PayloadBuildError:
        raise
    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        if "operation" in error_msg:
            raise NoOperationError()
        raise PayloadBuildError("", str(e))


async def download_payload(
    mythic_instance: mythic_classes.Mythic,
    payload_uuid: str,
) -> DownloadPayloadResponse:
    """Download a built payload binary by UUID."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not payload_uuid or not payload_uuid.strip():
        raise PayloadNotFoundError(payload_uuid)

    # First verify payload exists and is built
    try:
        payload_data = await mythic.get_payload_by_uuid(
            mythic=mythic_instance,
            payload_uuid=payload_uuid,
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "failed to find" in error_msg:
            raise PayloadNotFoundError(payload_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise PayloadNotFoundError(payload_uuid)

    build_phase = payload_data.get("build_phase", "")
    if build_phase != "success":
        raise PayloadDownloadError(payload_uuid, f"Build not complete (phase: {build_phase})")

    # Download the binary
    try:
        content_bytes = await mythic.download_payload(
            mythic=mythic_instance,
            payload_uuid=payload_uuid,
        )

        if not content_bytes:
            raise PayloadDownloadError(payload_uuid, "Download returned empty content")

        content_base64 = base64.b64encode(content_bytes).decode("ascii")

        filename = "unknown"
        if filemetum := payload_data.get("filemetum"):
            filename = filemetum.get("filename_utf8", "unknown") or "unknown"

        return DownloadPayloadResponse(
            payload_uuid=payload_uuid,
            filename=filename,
            content=content_base64,
            size_bytes=len(content_bytes),
        )

    except PayloadDownloadError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise PayloadDownloadError(payload_uuid, str(e))


async def check_payload_config(
    mythic_instance: mythic_classes.Mythic,
    payload_uuid: str,
) -> PayloadConfigCheckResponse:
    """Validate a payload's C2 configuration."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not payload_uuid or not payload_uuid.strip():
        raise PayloadNotFoundError(payload_uuid)

    try:
        result = await mythic.payload_check_config(
            mythic=mythic_instance,
            payload_uuid=payload_uuid,
        )

        return PayloadConfigCheckResponse(
            payload_uuid=payload_uuid,
            status=result.get("status", ""),
            error=result.get("error", "") or "",
            output=result.get("output", "") or "",
        )

    except NoOperationError:
        raise
    except PayloadNotFoundError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "failed to find" in error_msg or "not found" in error_msg:
            raise PayloadNotFoundError(payload_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise ConnectionError(f"Failed to check payload config: {e}")


async def payload_redirect_rules(
    mythic_instance: mythic_classes.Mythic,
    payload_uuid: str,
) -> PayloadConfigCheckResponse:
    """Get redirect rules for a payload."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not payload_uuid or not payload_uuid.strip():
        raise PayloadNotFoundError(payload_uuid)

    try:
        result = await mythic.payload_redirect_rules(
            mythic=mythic_instance,
            payload_uuid=payload_uuid,
        )

        return PayloadConfigCheckResponse(
            payload_uuid=payload_uuid,
            status=result.get("status", ""),
            error=result.get("error", "") or "",
            output=result.get("output", "") or "",
        )

    except NoOperationError:
        raise
    except PayloadNotFoundError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "failed to find" in error_msg or "not found" in error_msg:
            raise PayloadNotFoundError(payload_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise ConnectionError(f"Failed to get redirect rules: {e}")


DELETE_PAYLOAD_MUTATION = """
mutation PayloadsDeletePayloadMutation($payload_uuid: String!) {
  updatePayload(payload_uuid: $payload_uuid, deleted: true) {
    status
    error
    id
  }
}
"""


async def delete_payload(
    mythic_instance: mythic_classes.Mythic,
    payload_uuid: str,
) -> DeletePayloadResponse:
    """Soft-delete a payload by UUID (sets deleted flag to true)."""
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not payload_uuid or not payload_uuid.strip():
        raise PayloadNotFoundError(payload_uuid)

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=DELETE_PAYLOAD_MUTATION,
            variables={"payload_uuid": payload_uuid},
        )

        update_result = result.get("updatePayload", {})
        status = update_result.get("status", "")
        error = update_result.get("error", "")

        if status != "success":
            raise PayloadError(f"Delete failed: {error or 'unknown error'}")

        return DeletePayloadResponse(payload_uuid=payload_uuid)

    except PayloadNotFoundError:
        raise
    except NoOperationError:
        raise
    except PayloadError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "failed to find" in error_msg or "not found" in error_msg:
            raise PayloadNotFoundError(payload_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise ConnectionError(f"Failed to delete payload: {e}")


# --- Tool Entry Points ---


async def core_list_payloads(ctx: Context) -> ListPayloadsResponse:
    """List all payloads in the current Mythic operation.

    Returns UUID, agent type, build status, OS, description, and C2 profiles
    for each payload. Includes auto-generated and deleted payloads with metadata flags.
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_payloads(mythic_ctx.mythic)
    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_payloads")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_get_payload(ctx: Context, payload_uuid: str) -> GetPayloadResponse:
    """Get detailed information about a specific Mythic payload by UUID.

    Returns build phase, build messages, operator, file metadata, C2 profile details,
    and other configuration for the specified payload.

    Args:
        payload_uuid: UUID of the payload to retrieve
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_payload_by_uuid(mythic_ctx.mythic, payload_uuid)
    except PayloadNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_payload")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_create_payload(
    ctx: Context,
    payload_type_name: str,
    filename: str,
    operating_system: str,
    c2_profiles: str,
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
        c2_profiles: JSON array of C2 profile configs, e.g. [{"c2_profile": "http", "c2_profile_parameters": {"callback_host": "https://..."}}]
        description: Payload description (optional)
        commands: JSON array of command names to include (optional)
        build_parameters: JSON array of build params [{"name": "...", "value": "..."}] (optional)
        include_all_commands: Include all commands for the agent type (optional, default false)
        timeout: Build timeout in seconds, 30-600 (optional, default 300)
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    # Validate timeout range
    if timeout < 30 or timeout > 600:
        return CreatePayloadErrorResponse(
            error=f"Timeout must be between 30 and 600 seconds, got {timeout}",
            error_type="invalid_input",
        )

    # Parse JSON inputs
    try:
        parsed_c2 = _parse_c2_profiles_json(c2_profiles)
    except InvalidJSONError as e:
        return CreatePayloadErrorResponse(error=str(e), error_type="invalid_input")

    try:
        parsed_build_params = _parse_build_parameters_json(build_parameters)
    except InvalidJSONError as e:
        return CreatePayloadErrorResponse(error=str(e), error_type="invalid_input")

    try:
        parsed_commands = _parse_commands_json(commands)
    except InvalidJSONError as e:
        return CreatePayloadErrorResponse(error=str(e), error_type="invalid_input")

    try:
        return await create_payload(
            mythic_ctx.mythic,
            payload_type_name=payload_type_name,
            filename=filename,
            operating_system=operating_system,
            c2_profiles=parsed_c2,
            commands=parsed_commands or None,
            build_parameters=parsed_build_params or None,
            description=description,
            include_all_commands=include_all_commands,
            timeout=timeout,
        )

    except NoOperationError as e:
        return CreatePayloadErrorResponse(error=str(e), error_type="no_operation")
    except PayloadBuildError as e:
        return CreatePayloadErrorResponse(
            error=str(e), error_type="build_failed", uuid=e.uuid or None
        )
    except ConnectionError as e:
        return CreatePayloadErrorResponse(error=str(e), error_type="connection_error")
    except Exception as e:
        logger.exception("Unexpected error in core_create_payload")
        return CreatePayloadErrorResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}",
            error_type="unexpected_error",
        )


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
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await download_payload(mythic_ctx.mythic, payload_uuid)

    except PayloadNotFoundError as e:
        return DownloadPayloadErrorResponse(
            error=str(e), error_type="not_found", payload_uuid=payload_uuid
        )
    except PayloadDownloadError as e:
        return DownloadPayloadErrorResponse(
            error=str(e), error_type="build_incomplete", payload_uuid=payload_uuid
        )
    except NoOperationError as e:
        return DownloadPayloadErrorResponse(
            error=str(e), error_type="no_operation", payload_uuid=payload_uuid
        )
    except ConnectionError as e:
        return DownloadPayloadErrorResponse(
            error=str(e), error_type="connection_error", payload_uuid=payload_uuid
        )
    except Exception as e:
        logger.exception("Unexpected error in core_download_payload")
        return DownloadPayloadErrorResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}",
            error_type="unexpected_error",
            payload_uuid=payload_uuid,
        )


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
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await check_payload_config(mythic_ctx.mythic, payload_uuid)
    except PayloadNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_check_payload_config")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


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
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await payload_redirect_rules(mythic_ctx.mythic, payload_uuid)
    except PayloadNotFoundError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_payload_redirect_rules")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_delete_payload(
    ctx: Context,
    payload_uuid: str,
) -> DeletePayloadResponse | DeletePayloadErrorResponse:
    """Soft-delete a payload from the current Mythic operation.

    Marks the payload as deleted. This is reversible through the Mythic UI.

    Args:
        payload_uuid: UUID of the payload to delete
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await delete_payload(mythic_ctx.mythic, payload_uuid)

    except PayloadNotFoundError as e:
        return DeletePayloadErrorResponse(
            error=str(e), error_type="not_found", payload_uuid=payload_uuid
        )
    except NoOperationError as e:
        return DeletePayloadErrorResponse(
            error=str(e), error_type="no_operation", payload_uuid=payload_uuid
        )
    except ConnectionError as e:
        return DeletePayloadErrorResponse(
            error=str(e), error_type="connection_error", payload_uuid=payload_uuid
        )
    except PayloadError as e:
        return DeletePayloadErrorResponse(
            error=str(e), error_type="delete_failed", payload_uuid=payload_uuid
        )
    except Exception as e:
        logger.exception("Unexpected error in core_delete_payload")
        return DeletePayloadErrorResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}",
            error_type="unexpected_error",
            payload_uuid=payload_uuid,
        )
