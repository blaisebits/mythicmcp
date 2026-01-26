"""Arachne agent plugin for MythicMCP.

Arachne is a webshell agent supporting ASPX, PHP, and JSP payloads
for Windows and Linux systems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from mythicmcp.models import PluginToolErrorResponse, PluginToolSuccessResponse
from mythicmcp.plugins.base import AgentPlugin, ToolDefinition
from mythicmcp.plugins.executor import execute_with_validation

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context


# --- Parameter Models ---


class ArachneShellParams(BaseModel):
    """Parameters for arachne_shell tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    command: str = Field(..., description="Command to execute")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ArachnePwdParams(BaseModel):
    """Parameters for arachne_pwd tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ArachneLsParams(BaseModel):
    """Parameters for arachne_ls tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(default=".", description="Path to list (default: current directory)")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ArachneCdParams(BaseModel):
    """Parameters for arachne_cd tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to change to")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ArachneRmParams(BaseModel):
    """Parameters for arachne_rm tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to file to remove")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ArachneDownloadParams(BaseModel):
    """Parameters for arachne_download tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to file to download")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


class ArachneUploadParams(BaseModel):
    """Parameters for arachne_upload tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    remote_path: str = Field(..., description="Destination path on target")
    file_contents: str = Field(..., description="Base64-encoded file contents")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


class ArachneExecuteAssemblyParams(BaseModel):
    """Parameters for arachne_execute_assembly tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    assembly_name: str = Field(..., description="Name of registered .NET assembly")
    assembly_arguments: str = Field(default="", description="Arguments to pass to assembly")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


# --- Tool Handlers ---


async def _shell_handler(
    ctx: Context, params: ArachneShellParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a shell command."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="shell",
        parameters={"command": params.command},
        timeout=params.timeout,
    )


async def _pwd_handler(
    ctx: Context, params: ArachnePwdParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Get current working directory."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="pwd",
        parameters={},
        timeout=params.timeout,
    )


async def _ls_handler(
    ctx: Context, params: ArachneLsParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """List directory contents."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="ls",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _cd_handler(
    ctx: Context, params: ArachneCdParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Change working directory."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="cd",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _rm_handler(
    ctx: Context, params: ArachneRmParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Remove a file."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="rm",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _download_handler(
    ctx: Context, params: ArachneDownloadParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Download a file from target."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="download",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _upload_handler(
    ctx: Context, params: ArachneUploadParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Upload a file to target."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="upload",
        parameters={
            "remote_path": params.remote_path,
            "file_contents": params.file_contents,
        },
        timeout=params.timeout,
    )


async def _execute_assembly_handler(
    ctx: Context, params: ArachneExecuteAssemblyParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a .NET assembly (ASPX only)."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="arachne",
        command_name="execute_assembly",
        parameters={
            "assembly_name": params.assembly_name,
            "assembly_arguments": params.assembly_arguments,
        },
        timeout=params.timeout,
    )


# --- Plugin Class ---


class ArachnePlugin(AgentPlugin):
    """Arachne webshell agent plugin.

    Provides tools for executing commands on Arachne callbacks including
    shell commands, file operations, and .NET assembly execution (ASPX only).
    Supports Windows and Linux systems through ASPX, PHP, and JSP payloads.
    """

    agent_name: str = "arachne"
    agent_description: str = "Arachne webshell agent (ASPX/PHP/JSP)"
    supported_os: list[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.supported_os is None:
            object.__setattr__(self, "supported_os", ["Windows", "Linux"])

    def __init__(self) -> None:
        super().__init__()
        self.agent_name = "arachne"
        self.agent_description = "Arachne webshell agent (ASPX/PHP/JSP)"
        self.supported_os = ["Windows", "Linux"]

    def get_tools(self) -> list[ToolDefinition]:
        """Return list of Arachne tools."""
        return [
            ToolDefinition(
                name="shell",
                description="Execute a shell command on an Arachne webshell callback",
                parameters=ArachneShellParams,
                handler=_shell_handler,
            ),
            ToolDefinition(
                name="pwd",
                description="Get current working directory of an Arachne webshell",
                parameters=ArachnePwdParams,
                handler=_pwd_handler,
            ),
            ToolDefinition(
                name="ls",
                description="List directory contents on an Arachne webshell",
                parameters=ArachneLsParams,
                handler=_ls_handler,
            ),
            ToolDefinition(
                name="cd",
                description="Change working directory on an Arachne webshell",
                parameters=ArachneCdParams,
                handler=_cd_handler,
            ),
            ToolDefinition(
                name="rm",
                description="Remove a file on an Arachne webshell",
                parameters=ArachneRmParams,
                handler=_rm_handler,
            ),
            ToolDefinition(
                name="download",
                description="Download a file from an Arachne webshell callback",
                parameters=ArachneDownloadParams,
                handler=_download_handler,
            ),
            ToolDefinition(
                name="upload",
                description="Upload a file to an Arachne webshell callback",
                parameters=ArachneUploadParams,
                handler=_upload_handler,
            ),
            ToolDefinition(
                name="execute_assembly",
                description="Execute a .NET assembly on an Arachne ASPX webshell (Windows only)",
                parameters=ArachneExecuteAssemblyParams,
                handler=_execute_assembly_handler,
            ),
        ]
