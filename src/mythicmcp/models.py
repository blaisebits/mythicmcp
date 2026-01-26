"""Pydantic models for MythicMCP tool responses.

All models include timestamps per FR-008 to indicate when data was retrieved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


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
