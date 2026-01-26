"""Apollo agent plugin for MythicMCP.

Apollo is a Windows C# agent supporting shell commands, .NET assembly execution,
file operations, and more.
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


class ApolloShellParams(BaseModel):
    """Parameters for apollo_shell tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    command: str = Field(..., description="Shell command to execute via cmd.exe")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloPwdParams(BaseModel):
    """Parameters for apollo_pwd tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloLsParams(BaseModel):
    """Parameters for apollo_ls tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(default=".", description="Path to list (default: current directory)")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloCdParams(BaseModel):
    """Parameters for apollo_cd tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to change to")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloCatParams(BaseModel):
    """Parameters for apollo_cat tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to file to read")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloPsParams(BaseModel):
    """Parameters for apollo_ps tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloRunParams(BaseModel):
    """Parameters for apollo_run tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    executable: str = Field(..., description="Path to executable")
    arguments: str = Field(default="", description="Arguments to pass to executable")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")


class ApolloDownloadParams(BaseModel):
    """Parameters for apollo_download tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to file to download")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


class ApolloExecuteAssemblyParams(BaseModel):
    """Parameters for apollo_execute_assembly tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    assembly_name: str = Field(..., description="Name of registered .NET assembly (e.g., 'Seatbelt.exe')")
    assembly_arguments: str = Field(default="", description="Arguments to pass to assembly")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


class ApolloScreenshotParams(BaseModel):
    """Parameters for apollo_screenshot tool."""

    callback_id: int = Field(..., description="Callback ID to execute on")
    timeout: int = Field(default=120, ge=30, le=300, description="Timeout in seconds")


# --- Tool Handlers ---


async def _shell_handler(
    ctx: Context, params: ApolloShellParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a shell command via cmd.exe."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="shell",
        parameters={"command": params.command},
        timeout=params.timeout,
    )


async def _pwd_handler(
    ctx: Context, params: ApolloPwdParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Get current working directory."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="pwd",
        parameters={},
        timeout=params.timeout,
    )


async def _ls_handler(
    ctx: Context, params: ApolloLsParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """List directory contents."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="ls",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _cd_handler(
    ctx: Context, params: ApolloCdParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Change working directory."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="cd",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _cat_handler(
    ctx: Context, params: ApolloCatParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Read file contents."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="cat",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _ps_handler(
    ctx: Context, params: ApolloPsParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """List running processes."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="ps",
        parameters={},
        timeout=params.timeout,
    )


async def _run_handler(
    ctx: Context, params: ApolloRunParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a program without cmd.exe wrapper."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="run",
        parameters={"executable": params.executable, "arguments": params.arguments},
        timeout=params.timeout,
    )


async def _download_handler(
    ctx: Context, params: ApolloDownloadParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Download a file from target."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="download",
        parameters={"path": params.path},
        timeout=params.timeout,
    )


async def _execute_assembly_handler(
    ctx: Context, params: ApolloExecuteAssemblyParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Execute a .NET assembly."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="execute_assembly",
        parameters={
            "assembly_name": params.assembly_name,
            "assembly_arguments": params.assembly_arguments,
        },
        timeout=params.timeout,
    )


async def _screenshot_handler(
    ctx: Context, params: ApolloScreenshotParams
) -> PluginToolSuccessResponse | PluginToolErrorResponse:
    """Capture a screenshot."""
    return await execute_with_validation(
        ctx=ctx,
        callback_id=params.callback_id,
        expected_agent_type="apollo",
        command_name="screenshot",
        parameters={},
        timeout=params.timeout,
    )


# --- Plugin Class ---


class ApolloPlugin(AgentPlugin):
    """Apollo Windows C# agent plugin.

    Provides tools for executing commands on Apollo callbacks including
    shell commands, file operations, process listing, and .NET assembly execution.
    """

    agent_name: str = "apollo"
    agent_description: str = "Apollo Windows C# agent"
    supported_os: list[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.supported_os is None:
            object.__setattr__(self, "supported_os", ["Windows"])

    def __init__(self) -> None:
        super().__init__()
        self.agent_name = "apollo"
        self.agent_description = "Apollo Windows C# agent"
        self.supported_os = ["Windows"]

    def get_tools(self) -> list[ToolDefinition]:
        """Return list of Apollo tools."""
        return [
            ToolDefinition(
                name="shell",
                description="Execute a shell command via cmd.exe on an Apollo callback",
                parameters=ApolloShellParams,
                handler=_shell_handler,
            ),
            ToolDefinition(
                name="pwd",
                description="Get current working directory of an Apollo callback",
                parameters=ApolloPwdParams,
                handler=_pwd_handler,
            ),
            ToolDefinition(
                name="ls",
                description="List directory contents on an Apollo callback",
                parameters=ApolloLsParams,
                handler=_ls_handler,
            ),
            ToolDefinition(
                name="cd",
                description="Change working directory on an Apollo callback",
                parameters=ApolloCdParams,
                handler=_cd_handler,
            ),
            ToolDefinition(
                name="cat",
                description="Read file contents on an Apollo callback",
                parameters=ApolloCatParams,
                handler=_cat_handler,
            ),
            ToolDefinition(
                name="ps",
                description="List running processes on an Apollo callback",
                parameters=ApolloPsParams,
                handler=_ps_handler,
            ),
            ToolDefinition(
                name="run",
                description="Execute a program without cmd.exe wrapper on an Apollo callback",
                parameters=ApolloRunParams,
                handler=_run_handler,
            ),
            ToolDefinition(
                name="download",
                description="Download a file from an Apollo callback",
                parameters=ApolloDownloadParams,
                handler=_download_handler,
            ),
            ToolDefinition(
                name="execute_assembly",
                description="Execute a .NET assembly on an Apollo callback",
                parameters=ApolloExecuteAssemblyParams,
                handler=_execute_assembly_handler,
            ),
            ToolDefinition(
                name="screenshot",
                description="Take a screenshot on an Apollo callback",
                parameters=ApolloScreenshotParams,
                handler=_screenshot_handler,
            ),
        ]
