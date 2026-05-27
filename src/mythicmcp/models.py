"""Pydantic models for MythicMCP tool responses.

All models include timestamps per FR-008 to indicate when data was retrieved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

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


class GetTaskOutputResponse(BaseModel):
    """Response for core_get_task_output tool."""

    task_display_id: int = Field(description="Task display ID queried")
    output: list[TaskOutput] = Field(
        default_factory=list, description="All output responses for the task"
    )
    count: int = Field(description="Number of output entries returned")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class TaskSummary(BaseModel):
    """Summary view of a Mythic task."""

    task_id: int = Field(description="Internal Mythic task ID")
    task_display_id: int = Field(description="Operator-facing Mythic task display ID")
    command_name: str = Field(description="Command that was issued")
    status: str = Field(
        description="Raw Mythic task status snapshot. This can lag behind the latest task output."
    )
    completed: bool = Field(description="Whether task has finished")
    timestamp: Optional[str] = Field(
        default=None, description="When task was issued (ISO 8601)"
    )
    operator: str = Field(default="", description="Operator who issued the task")
    original_params: str = Field(default="", description="Raw parameters as submitted")
    display_params: str = Field(
        default="", description="Human-readable parameter summary"
    )
    callback_id: int = Field(
        description="Canonical callback_id this task ran on"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )


class ListCallbackTasksResponse(BaseModel):
    """Response for core_list_callback_tasks tool."""

    callback_id: int = Field(
        description="Canonical callback_id that was queried"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id for the queried callback"
    )
    tasks: list[TaskSummary] = Field(description="Tasks issued to this callback")
    count: int = Field(description="Total number of tasks returned")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class TaskCallbackInfo(BaseModel):
    """Callback identifiers attached to a task."""

    callback_id: int = Field(description="Canonical callback_id")
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )
    hostname: str = Field(default="", description="Target hostname")
    username: str = Field(default="", description="User context")
    agent_type: str = Field(default="", description="Payload type name")


class GetTaskCallbackResponse(BaseModel):
    """Response for core_get_task_callback tool."""

    task_id: int = Field(description="Internal task ID")
    task_display_id: int = Field(description="Task display ID that was queried")
    command_name: str = Field(description="Command that was issued")
    status: str = Field(
        description="Raw Mythic task status at query time. This can lag behind the latest task output."
    )
    callback: TaskCallbackInfo = Field(
        description="Callback the task was issued to"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class InteractiveTaskEntry(BaseModel):
    """A single interactive task (keystroke or command) within a PTY session."""

    id: int = Field(description="Internal task ID")
    display_id: int = Field(description="Human-readable task display ID")
    interactive_task_type: int = Field(description="Raw interactive type enum value")
    interactive_task_type_label: str = Field(
        description="Decoded label (e.g. Input, CtrlC, Exit)"
    )
    original_params: str = Field(default="", description="Raw parameters as submitted")
    display_params: str = Field(
        default="", description="Human-readable parameter summary"
    )
    status: str = Field(default="", description="Task status")
    timestamp: Optional[str] = Field(
        default=None, description="When task was issued (ISO 8601)"
    )
    command_name: str = Field(default="", description="Command name")


class ListInteractiveTasksResponse(BaseModel):
    """Response for core_list_interactive_tasks tool."""

    parent_task_display_id: int = Field(
        description="Display ID of the parent PTY task"
    )
    parent_command_name: str = Field(
        description="Command that opened the session (e.g. pty)"
    )
    entries: list[InteractiveTaskEntry] = Field(
        description="Interactive child tasks in chronological order"
    )
    count: int = Field(description="Number of entries returned")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class InteractiveSessionEvent(BaseModel):
    """A single event in a reconstructed interactive session transcript."""

    task_display_id: int = Field(
        description="Display ID of the task that produced this event"
    )
    event_type: str = Field(
        description="Decoded event type (Input, Output, CtrlC, etc.)"
    )
    content: str = Field(
        default="",
        description="Typed command for Input events, terminal output for Output events",
    )
    timestamp: Optional[str] = Field(
        default=None, description="When event occurred (ISO 8601)"
    )


class GetInteractiveSessionResponse(BaseModel):
    """Response for core_get_interactive_session tool."""

    parent_task_display_id: int = Field(
        description="Display ID of the parent PTY task"
    )
    parent_command_name: str = Field(
        description="Command that opened the session (e.g. pty)"
    )
    callback_id: int = Field(
        description="Canonical callback_id the session ran on"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )
    events: list[InteractiveSessionEvent] = Field(
        description="Chronological list of session events (inputs + outputs)"
    )
    event_count: int = Field(description="Total number of events")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


# --- File Browser Models ---


class FileBrowserEntry(BaseModel):
    """A single file or directory entry from Mythic's file browser."""

    id: int = Field(description="Internal entry ID")
    name: str = Field(description="File or directory name")
    full_path: str = Field(description="Complete path on target system")
    parent_path: str = Field(default="", description="Parent directory path")
    host: str = Field(description="Hostname where entry was found")
    is_file: bool = Field(description="True for files, False for directories")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    permissions: str = Field(default="", description="Permission string (e.g. rwxr-xr-x)")
    access_time: Optional[str | int] = Field(
        default=None, description="Last access time (ISO string or Unix ms)"
    )
    modify_time: Optional[str | int] = Field(
        default=None, description="Last modification time (ISO string or Unix ms)"
    )
    comment: str = Field(default="", description="Operator comment")
    success: Optional[bool] = Field(default=None, description="Whether retrieval succeeded")
    timestamp: Optional[str] = Field(
        default=None, description="When entry was recorded (ISO 8601)"
    )


class GetFileBrowserByTaskResponse(BaseModel):
    """Response for core_get_file_browser_by_task tool."""

    task_display_id: int = Field(description="Task display ID that was queried")
    entries: list[FileBrowserEntry] = Field(
        description="File browser entries created by this task"
    )
    count: int = Field(description="Number of entries returned")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class ListFileBrowserResponse(BaseModel):
    """Response for core_list_file_browser tool."""

    host: str = Field(description="Hostname that was queried")
    path: Optional[str] = Field(
        default=None, description="Path filter applied (None = all entries)"
    )
    entries: list[FileBrowserEntry] = Field(
        description="File browser entries matching the query"
    )
    count: int = Field(description="Number of entries returned")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class PluginToolSuccessResponse(BaseModel):
    """Successful plugin tool execution."""

    success: bool = True
    task_id: int = Field(description="Internal Mythic task ID")
    task_display_id: int | None = Field(
        default=None,
        description="Operator-facing Mythic task display ID shown in the UI",
    )
    output: str
    execution_time_ms: float


class PluginToolErrorResponse(BaseModel):
    """Failed plugin tool execution."""

    success: bool = False
    error: str
    error_type: str  # "agent_mismatch", "callback_not_found", "execution_failed", "timeout"
    callback_id: int | None = None
    task_id: int | None = Field(
        default=None,
        description="Internal Mythic task ID if a task was created",
    )
    task_display_id: int | None = Field(
        default=None,
        description="Operator-facing Mythic task display ID if a task was created",
    )


class CallbackAgentInfo(BaseModel):
    """Agent type information for a callback."""

    callback_id: int
    display_id: int
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

    callback_id: int = Field(
        description="Canonical callback_id for follow-on MCP tasking and lookups"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id shown in the Mythic UI"
    )
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

    callback_id: int = Field(
        description="Canonical callback_id for follow-on MCP tasking and lookups"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id shown in the Mythic UI"
    )
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
    sleep_info: str = Field(default="", description="Current sleep/jitter configuration")
    last_checkin: str | None = Field(default=None, description="Most recent callback checkin timestamp")
    time_since_last_checkin: str | None = Field(
        default=None,
        description="Human-readable elapsed time since the most recent checkin",
    )
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


class CallbackCommandSummary(BaseModel):
    """Summary view of a command loaded on a specific callback."""

    command_name: str = Field(description="Loaded Mythic command name")
    source: str = Field(
        description="Originating payload or service name for this command"
    )
    is_native: bool = Field(
        description="Whether the command source matches the callback's native agent type"
    )
    usage: str = Field(
        description="Display/help usage text from Mythic. This may not match the exact `arguments` payload format."
    )
    description: str = Field(description="Command description from Mythic")
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw Mythic command attributes dictionary",
    )


class CallbackCommandParameter(BaseModel):
    """Parameter metadata for a callback-loaded command."""

    name: str = Field(description="Internal parameter name")
    cli_name: str = Field(description="CLI parameter name")
    display_name: str = Field(description="Human-readable parameter name")
    description: str = Field(description="Parameter description")
    placeholder: str = Field(
        default="",
        description="Suggested placeholder value from Mythic, if provided",
    )
    example: str = Field(
        default="",
        description="Suggested example value from Mythic, if provided",
    )
    type: str = Field(description="Mythic parameter type")
    default_value: str = Field(default="", description="Default parameter value")
    required: bool = Field(description="Whether the parameter is required")
    parameter_group_name: str = Field(description="Mythic parameter group name")
    ui_position: int = Field(description="Mythic UI ordering index")
    choices: list[Any] = Field(
        default_factory=list,
        description="Static choices for choose-one/choose-multiple parameters",
    )
    choices_are_all_commands: bool = Field(
        default=False,
        description="Whether choices should include all commands for the agent",
    )
    choices_are_loaded_commands: bool = Field(
        default=False,
        description="Whether choices should include only commands loaded on the callback",
    )
    choice_filter_by_command_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Attribute filters Mythic applies when building command choices",
    )
    supported_agents: list[str] = Field(
        default_factory=list,
        description="Agent types this parameter applies to",
    )
    supported_agent_build_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Build-parameter filters for this parameter",
    )
    dynamic_query_function: str = Field(
        default="",
        description="Dynamic Mythic query function name, if any",
    )


class CallbackCommandDetail(CallbackCommandSummary):
    """Detailed view of a command loaded on a callback."""

    parameters: list[CallbackCommandParameter] = Field(
        default_factory=list,
        description="Ordered command parameters from Mythic",
    )
    argument_mode: Literal["cli", "json_object"] = Field(
        description="Authoritative execution hint for how to build `arguments`: raw CLI text or a JSON object string"
    )
    execution_usage: str = Field(
        description="Exact MCP `arguments` payload string to send for a minimal valid execution"
    )
    example_arguments: str = Field(
        description="Recommended starter `arguments` payload string matching `argument_mode`"
    )
    zero_arg_example: str | None = Field(
        default=None,
        description="Empty-string example for true zero-arg commands, if applicable",
    )
    execution_notes: str = Field(
        description="Short execution guidance for how to build the `arguments` string"
    )


class ListCallbackCommandsResponse(BaseModel):
    """Response for core_list_callback_commands tool."""

    callback_id: int = Field(
        description="Canonical callback_id that was queried"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )
    agent_type: str = Field(description="Native payload type name for the callback")
    source: str = Field(
        default="",
        description="Source filter applied to the results, if any",
    )
    commands: list[CallbackCommandSummary] = Field(
        description="Loaded commands available on this callback"
    )
    count: int = Field(description="Number of commands returned")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class GetCallbackCommandResponse(BaseModel):
    """Response for core_get_callback_command tool."""

    callback_id: int = Field(
        description="Canonical callback_id that was queried"
    )
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )
    agent_type: str = Field(description="Native payload type name for the callback")
    command: CallbackCommandDetail = Field(
        description="Detailed metadata for the loaded command"
    )
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class ExecuteCallbackCommandSuccessResponse(BaseModel):
    """Successful generic callback command execution."""

    success: bool = True
    callback_id: int = Field(description="Canonical callback_id the task ran on")
    display_id: int = Field(
        description="Operator-facing callback display_id for UI correlation only"
    )
    command_name: str = Field(description="Loaded command name that was executed")
    source: str = Field(description="Originating payload or service name")
    task_id: int = Field(description="Internal Mythic task ID")
    task_display_id: int = Field(
        description="Operator-facing Mythic task display ID"
    )
    output: str = Field(description="Combined decoded task output")
    execution_time_ms: float = Field(description="End-to-end execution time in milliseconds")


class ExecuteCallbackCommandErrorResponse(BaseModel):
    """Failed generic callback command execution."""

    success: bool = False
    error: str = Field(description="Human-readable error message")
    error_type: str = Field(
        description="Stable error type such as ambiguous_command or command_not_loaded"
    )
    callback_id: int | None = Field(
        default=None,
        description="Canonical callback_id involved in the failed request",
    )
    display_id: int | None = Field(
        default=None,
        description="Operator-facing callback display_id if resolved",
    )
    command_name: str | None = Field(
        default=None,
        description="Command name involved in the failed request",
    )
    source: str | None = Field(
        default=None,
        description="Originating payload or service name, if resolved",
    )
    task_id: int | None = Field(
        default=None,
        description="Internal Mythic task ID if a task was created",
    )
    task_display_id: int | None = Field(
        default=None,
        description="Operator-facing Mythic task display ID if a task was created",
    )


# --- Operation Models ---


class OperationInfo(BaseModel):
    """Mythic operation metadata."""

    id: int = Field(description="Operation ID")
    name: str = Field(description="Operation name")
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
    accessible_operations: list[OperationSummary] = Field(
        default_factory=list,
        description="Operations accessible to the authenticated user",
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
    callback_id: Optional[int] = Field(
        default=None, description="Canonical callback_id that sourced the file"
    )
    display_id: Optional[int] = Field(
        default=None,
        description="Operator-facing callback display_id for the source callback",
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
        description="Error category: no_operation, build_failed, connection_error, timeout, invalid_input, payload_type_unavailable"
    )
    uuid: Optional[str] = Field(default=None, description="Payload UUID if available")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DeletePayloadResponse(BaseModel):
    """Response for core_delete_payload tool (success case)."""

    success: bool = Field(default=True, description="Whether delete succeeded")
    payload_uuid: str = Field(description="Payload UUID")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DeletePayloadErrorResponse(BaseModel):
    """Response for core_delete_payload tool (error case)."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(
        description="Error category: not_found, no_operation, connection_error"
    )
    payload_uuid: str = Field(description="Requested payload UUID")
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


# --- Dynamic Agent Loading Models ---


class AvailableAgentInfo(PluginInfo):
    """Information about an agent available for dynamic loading."""

    loaded: bool = Field(description="Whether agent tools are currently registered with MCP")


class ListAvailableAgentsResponse(BaseModel):
    """Response for list_available_agents tool."""

    agents: list[AvailableAgentInfo] = Field(description="All available agents")
    total_count: int = Field(description="Total number of available agents")
    loaded_count: int = Field(description="Number of agents currently loaded")
    load_errors: list[PluginLoadErrorInfo] = Field(
        default_factory=list, description="Plugins that failed to load"
    )
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class LoadAgentToolsResponse(BaseModel):
    """Response for load_agent_tools tool (success case)."""

    success: bool = Field(default=True, description="Whether load succeeded")
    agent_name: str = Field(description="Agent that was loaded")
    tools_loaded: int = Field(description="Number of tools registered")
    tool_names: list[str] = Field(description="Names of registered tools")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class AgentToolsErrorResponse(BaseModel):
    """Error response for agent tool load/unload operations."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(description="Error category: not_found, already_loaded, not_loaded")
    agent_name: str = Field(description="Requested agent name")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class UnloadAgentToolsResponse(BaseModel):
    """Response for unload_agent_tools tool (success case)."""

    success: bool = Field(default=True, description="Whether unload succeeded")
    agent_name: str = Field(description="Agent that was unloaded")
    tools_removed: int = Field(description="Number of tools removed")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DevReloadResponse(BaseModel):
    """Response for dev_reload_runtime tool."""

    success: bool = Field(default=True, description="Whether reload completed")
    modules_reloaded: list[str] = Field(
        default_factory=list,
        description="Python modules reloaded in-place",
    )
    module_count: int = Field(description="Number of Python modules reloaded")
    reloaded_agents: list[str] = Field(
        default_factory=list,
        description="Agent namespaces restored after plugin reload",
    )
    reloaded_tool_count: int = Field(
        description="Number of agent tool handlers re-registered"
    )
    available_agents: int = Field(
        description="Number of agent plugins available after reload"
    )
    plugin_load_errors: list[PluginLoadErrorInfo] = Field(
        default_factory=list,
        description="Plugin configs that failed to load during reload",
    )
    note: str = Field(
        default=(
            "Core tool schema additions still require the MythicMCP server "
            "process to restart once."
        ),
        description="Reload caveat for development",
    )
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


# --- C2 Profile Management Models ---


class C2ProfileInfo(BaseModel):
    """Information about a C2 profile on the Mythic server."""

    name: str = Field(description="Profile name (e.g., 'http', 'websocket', 'tcp')")
    description: str = Field(description="Profile description")
    is_p2p: bool = Field(description="Whether profile is peer-to-peer")
    running: bool = Field(description="Whether profile container is running")
    container_running: bool = Field(description="Whether profile Docker container is running")


class ListC2ProfilesResponse(BaseModel):
    """Response for core_list_c2_profiles tool."""

    profiles: list[C2ProfileInfo] = Field(description="Available C2 profiles")
    total_count: int = Field(description="Total number of profiles")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class C2ParameterDefinition(BaseModel):
    """Definition of a single C2 profile parameter."""

    name: str = Field(description="Parameter name")
    description: str = Field(description="Parameter description")
    default_value: str = Field(description="Default value (as string)")
    required: bool = Field(description="Whether parameter is required")
    randomize: bool = Field(default=False, description="Whether value is randomized")
    parameter_type: str = Field(description="Parameter type (e.g., 'String', 'ChooseOne', 'Boolean', 'Number', 'Date', 'Dictionary')")
    choices: list[Any] = Field(default_factory=list, description="Valid choices (strings for ChooseOne, dicts for Dictionary type)")


class GetC2ProfileParametersResponse(BaseModel):
    """Response for core_get_c2_profile_parameters tool."""

    profile_name: str = Field(description="C2 profile name")
    parameters: list[C2ParameterDefinition] = Field(description="Parameter definitions")
    parameter_count: int = Field(description="Number of parameters")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class C2InstanceSummary(BaseModel):
    """Summary of a saved C2 profile instance."""

    instance_name: str = Field(description="Name of the saved instance")
    c2_profile_name: str = Field(description="Associated C2 profile name")


class ListC2InstancesResponse(BaseModel):
    """Response for core_list_c2_instances tool."""

    instances: list[C2InstanceSummary] = Field(description="Saved C2 instances")
    total_count: int = Field(description="Total number of saved instances")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class GetC2InstanceResponse(BaseModel):
    """Response for core_get_c2_instance tool."""

    instance_name: str = Field(description="Instance name")
    c2_profile_name: str = Field(description="Associated C2 profile name")
    c2_parameters: dict = Field(description="Saved parameter values")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when data was retrieved (ISO 8601 UTC)",
    )


class CreateC2InstanceResponse(BaseModel):
    """Response for core_create_c2_instance tool."""

    success: bool = Field(default=True, description="Whether creation succeeded")
    instance_name: str = Field(description="Created instance name")
    c2_profile_name: str = Field(description="Associated C2 profile name")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class DeleteC2InstanceResponse(BaseModel):
    """Response for core_delete_c2_instance tool."""

    success: bool = Field(default=True, description="Whether deletion succeeded")
    instance_name: str = Field(description="Deleted instance name")
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of operation (ISO 8601 UTC)",
    )


class C2ProfileErrorResponse(BaseModel):
    """Error response for C2 profile operations."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error message")
    error_type: str = Field(description="Error category: not_found, connection_error, invalid_input")
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
