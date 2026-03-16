"""Pydantic models for MythicMCP tool responses.

All models include timestamps per FR-008 to indicate when data was retrieved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Plugin System Models ---


class TaskStatus(str, Enum):
    """Status of a Mythic task."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class ExecuteTaskRequest(BaseModel):
    """Request to execute an agent command."""

    callback_id: int = Field(..., description="Target callback ID")
    command_name: str = Field(..., description="Command to execute")
    parameters: dict = Field(default_factory=dict, description="Command parameters")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class TaskOutput(BaseModel):
    """Output from a task response."""

    response_id: int
    response: str
    timestamp: str | None = None


class ExecuteTaskResponse(BaseModel):
    """Response from executing an agent command."""

    task_id: int = Field(..., description="Mythic task ID")
    task_display_id: int = Field(..., description="Mythic task display ID")
    status: TaskStatus
    command: str
    agent_type: str
    callback_id: int
    output: list[TaskOutput] = Field(default_factory=list)
    error: str | None = None


class PluginToolSuccessResponse(BaseModel):
    """Successful plugin tool execution."""

    success: bool = True
    task_id: int
    output: str
    execution_time_ms: float


class PluginToolErrorResponse(BaseModel):
    """Failed plugin tool execution."""

    success: bool = False
    error: str
    error_type: str  # "agent_mismatch", "callback_not_found", "execution_failed", "timeout"
    callback_id: int | None = None
    task_id: int | None = None


class CallbackAgentInfo(BaseModel):
    """Agent type information for a callback."""

    callback_id: int
    agent_type: str
    active: bool


# --- Plugin List Response ---


class PluginInfo(BaseModel):
    """Information about a loaded plugin."""

    agent_name: str = Field(description="Agent identifier (e.g., 'apollo')")
    agent_description: str = Field(description="Human-readable description")
    tool_count: int = Field(description="Number of tools provided")
    supported_os: list[str] = Field(description="Supported operating systems")


class PluginLoadErrorInfo(BaseModel):
    """Information about a plugin that failed to load."""

    plugin_path: str = Field(description="Path or module that failed")
    error: str = Field(description="Error message")


class ListPluginsResponse(BaseModel):
    """Response for core_list_plugins tool."""

    plugins: list[PluginInfo] = Field(description="List of loaded plugins")
    total_count: int = Field(description="Total number of loaded plugins")
    load_errors: list[PluginLoadErrorInfo] = Field(
        default_factory=list, description="Plugins that failed to load"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


# --- Callback Models ---


class CallbackSummary(BaseModel):
    """Summary view of a Mythic callback for list operations."""

    id: int = Field(description="Internal callback ID")
    display_id: int = Field(description="Human-readable callback number")
    hostname: str = Field(description="Target hostname")
    username: str = Field(description="User context")
    agent_type: str = Field(description="Payload type name (e.g., apollo, poseidon)")
    os: str = Field(description="Operating system")
    internal_ip: str = Field(description="Internal IP address")
    integrity_level: int = Field(description="Windows integrity level (0-4)")
    process_name: str = Field(description="Process name")
    active: bool = Field(description="Whether callback is active")


class CallbackDetail(BaseModel):
    """Detailed view of a Mythic callback."""

    id: int = Field(description="Internal callback ID")
    display_id: int = Field(description="Human-readable callback number")
    hostname: str = Field(description="Target hostname")
    username: str = Field(description="User context")
    domain: str = Field(default="", description="Domain name (Windows)")
    internal_ip: str = Field(description="Internal IP address")
    external_ip: str = Field(default="", description="External/NAT IP")
    os: str = Field(description="Operating system")
    architecture: str = Field(default="", description="CPU architecture (x64, arm64)")
    process_id: int = Field(description="Process ID")
    process_name: str = Field(description="Process name")
    integrity_level: int = Field(description="Windows integrity level (0-4)")
    agent_type: str = Field(description="Payload type name")
    description: str = Field(default="", description="Callback description")
    active: bool = Field(description="Whether callback is active")


class ListCallbacksResponse(BaseModel):
    """Response for core_list_callbacks tool."""

    callbacks: list[CallbackSummary] = Field(description="List of active callbacks")
    count: int = Field(description="Total number of callbacks returned")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class GetCallbackResponse(BaseModel):
    """Response for core_get_callback tool."""

    callback: CallbackDetail = Field(description="Callback details")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


# --- Operation Models ---


class OperationInfo(BaseModel):
    """Mythic operation metadata."""

    id: int = Field(description="Operation ID")
    name: str = Field(description="Operation name")
    created_at: datetime = Field(description="Creation timestamp")
    complete: bool = Field(description="Whether operation is complete")


class OperatorInfo(BaseModel):
    """Mythic operator (user) information."""

    username: str = Field(description="Operator username")
    admin: bool = Field(description="Whether operator is admin")


class GetOperationResponse(BaseModel):
    """Response for core_get_operation tool."""

    operation: OperationInfo = Field(description="Operation details")
    operators: list[OperatorInfo] = Field(description="Operators assigned to operation")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class OperationSummary(BaseModel):
    """Summary view of a Mythic operation for list operations."""

    id: int = Field(description="Operation ID")
    name: str = Field(description="Operation name")
    complete: bool = Field(description="Whether operation is complete")
    admin_username: str = Field(description="Operation admin username")


class ListOperationsResponse(BaseModel):
    """Response for core_list_operations tool."""

    operations: list[OperationSummary] = Field(description="List of accessible operations")
    count: int = Field(description="Total number of operations")
    current_operation_id: Optional[int] = Field(
        default=None, description="Currently active operation ID (if set)"
    )
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class SetOperationResponse(BaseModel):
    """Response for core_set_operation tool."""

    success: bool = Field(description="Whether operation was set successfully")
    operation_id: int = Field(description="The operation ID that was set")
    operation_name: str = Field(description="The operation name that was set")
    message: str = Field(description="Status message")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when operation was set (ISO 8601 UTC)",
    )


# --- Connection Status Models ---


class CheckConnectionResponse(BaseModel):
    """Response for core_check_connection tool (success case)."""

    connected: bool = Field(description="Whether connection succeeded")
    server_url: str = Field(description="Mythic server URL (sanitized)")
    authenticated: bool = Field(description="Whether authentication succeeded")
    current_operation: Optional[str] = Field(
        default=None, description="Name of current operation (if set)"
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when check was performed (ISO 8601 UTC)",
    )


class CheckConnectionErrorResponse(BaseModel):
    """Response for core_check_connection tool (error case)."""

    connected: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: connection_failed, authentication_failed, timeout"
    )
    server_url: str = Field(description="Mythic server URL (sanitized)")
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when check was performed (ISO 8601 UTC)",
    )


# --- File Management Models ---


class UploadFileResponse(BaseModel):
    """Response for core_upload_file tool (success case)."""

    success: bool = Field(default=True, description="Whether upload succeeded")
    file_id: str = Field(description="UUID of uploaded file (for use in tasking)")
    filename: str = Field(description="Filename as stored")
    message: str = Field(description="Status message")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class UploadFileErrorResponse(BaseModel):
    """Response for core_upload_file tool (error case)."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: invalid_input, connection_error, no_operation"
    )
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DownloadFileResponse(BaseModel):
    """Response for core_download_file tool (success case)."""

    success: bool = Field(default=True, description="Whether download succeeded")
    file_uuid: str = Field(description="UUID of downloaded file")
    filename: str = Field(description="Original filename")
    content: str = Field(description="Base64-encoded file content")
    size_bytes: int = Field(description="File size in bytes (before encoding)")
    md5: Optional[str] = Field(default=None, description="MD5 hash if available")
    sha1: Optional[str] = Field(default=None, description="SHA1 hash if available")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DownloadFileErrorResponse(BaseModel):
    """Response for core_download_file tool (error case)."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: not_found, connection_error, no_operation"
    )
    file_uuid: str = Field(description="Requested UUID")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DownloadedFileSummary(BaseModel):
    """Summary of a file downloaded from an agent."""

    id: int = Field(description="Internal Mythic file ID")
    file_uuid: str = Field(description="File UUID (agent_file_id)")
    filename: str = Field(description="Filename (UTF-8)")
    full_remote_path: str = Field(description="Full path on target system")
    host: str = Field(description="Source hostname")
    size_bytes: Optional[int] = Field(default=None, description="File size if known")
    complete: bool = Field(description="Whether download completed")
    timestamp: datetime = Field(description="Download timestamp")
    md5: Optional[str] = Field(default=None, description="MD5 hash")
    sha1: Optional[str] = Field(default=None, description="SHA1 hash")
    comment: str = Field(default="", description="File comment")
    callback_id: Optional[int] = Field(default=None, description="Source callback ID")
    callback_display_id: Optional[int] = Field(
        default=None, description="Source callback display number"
    )
    task_id: Optional[int] = Field(
        default=None, description="Task that initiated download"
    )


class ListDownloadedFilesResponse(BaseModel):
    """Response for core_list_downloaded_files tool."""

    files: list[DownloadedFileSummary] = Field(description="List of downloaded files")
    count: int = Field(description="Total number of files")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of query (ISO 8601 UTC)",
    )


class UploadedFileSummary(BaseModel):
    """Summary of a file uploaded to Mythic."""

    id: int = Field(description="Internal Mythic file ID")
    file_id: str = Field(description="File UUID (agent_file_id) for tasking")
    filename: str = Field(description="Filename (UTF-8)")
    complete: bool = Field(description="Whether upload completed")
    timestamp: datetime = Field(description="Upload timestamp")
    comment: str = Field(default="", description="File comment")
    operator: str = Field(description="Username who uploaded")


class ListUploadedFilesResponse(BaseModel):
    """Response for core_list_uploaded_files tool."""

    files: list[UploadedFileSummary] = Field(description="List of uploaded files")
    count: int = Field(description="Total number of files")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of query (ISO 8601 UTC)",
    )


# --- Payload Models ---


class C2ProfileSummary(BaseModel):
    """Summary of a C2 profile associated with a payload."""

    name: str = Field(description="Profile name (e.g., 'http')")
    is_p2p: bool = Field(description="Whether this is a P2P profile")
    running: bool = Field(description="Whether the profile container is running")


class PayloadSummary(BaseModel):
    """Summary view of a Mythic payload for list operations."""

    uuid: str = Field(description="Payload UUID (primary identifier)")
    agent_type: str = Field(description="Payload type name (e.g., 'apollo')")
    build_phase: str = Field(description="Build status: 'building', 'success', 'error'")
    description: str = Field(default="", description="Operator-provided description")
    deleted: bool = Field(description="Whether payload has been deleted")
    auto_generated: bool = Field(description="Whether Mythic auto-generated this payload")
    creation_time: datetime = Field(description="When payload was created")
    os: str = Field(default="", description="Target operating system")
    c2_profiles: list[C2ProfileSummary] = Field(
        default_factory=list, description="Associated C2 profiles"
    )


class PayloadDetail(BaseModel):
    """Detailed view of a Mythic payload."""

    uuid: str = Field(description="Payload UUID")
    agent_type: str = Field(description="Payload type name")
    build_phase: str = Field(description="Build status")
    build_message: str = Field(default="", description="Build output message")
    build_stderr: str = Field(default="", description="Build stderr output")
    callback_alert: bool = Field(default=False, description="Whether callback alerts enabled")
    description: str = Field(default="", description="Operator-provided description")
    deleted: bool = Field(description="Whether payload has been deleted")
    auto_generated: bool = Field(description="Whether auto-generated")
    creation_time: datetime = Field(description="When payload was created")
    operator: str = Field(default="", description="Who created it")
    file_uuid: Optional[str] = Field(default=None, description="File UUID for download")
    filename: Optional[str] = Field(default=None, description="Built filename")
    os: str = Field(default="", description="Target operating system")
    c2_profiles: list[C2ProfileSummary] = Field(
        default_factory=list, description="Associated C2 profiles"
    )


class ListPayloadsResponse(BaseModel):
    """Response for core_list_payloads tool."""

    payloads: list[PayloadSummary] = Field(description="List of payloads")
    count: int = Field(description="Total number of payloads")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class GetPayloadResponse(BaseModel):
    """Response for core_get_payload tool."""

    payload: PayloadDetail = Field(description="Payload details")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class CreatePayloadResponse(BaseModel):
    """Response for core_create_payload tool (success case)."""

    success: bool = Field(default=True, description="Whether build succeeded")
    uuid: str = Field(description="Payload UUID")
    build_phase: str = Field(description="Terminal build status")
    build_message: str = Field(default="", description="Build output message")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class CreatePayloadErrorResponse(BaseModel):
    """Response for core_create_payload tool (error case)."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: no_operation, build_failed, connection_error, timeout, invalid_input"
    )
    uuid: Optional[str] = Field(default=None, description="Payload UUID if available")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DownloadPayloadResponse(BaseModel):
    """Response for core_download_payload tool (success case)."""

    success: bool = Field(default=True, description="Whether download succeeded")
    payload_uuid: str = Field(description="Payload UUID")
    filename: str = Field(description="Payload filename")
    content: str = Field(description="Base64-encoded payload binary")
    size_bytes: int = Field(description="File size in bytes (before encoding)")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DownloadPayloadErrorResponse(BaseModel):
    """Response for core_download_payload tool (error case)."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: not_found, build_incomplete, connection_error, no_operation"
    )
    payload_uuid: str = Field(description="Requested payload UUID")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class PayloadConfigCheckResponse(BaseModel):
    """Response for core_check_payload_config and core_payload_redirect_rules tools."""

    payload_uuid: str = Field(description="Payload UUID")
    status: str = Field(description="Check result: 'success' or 'error'")
    error: str = Field(default="", description="Error message if status is error")
    output: str = Field(default="", description="Result output text")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )
