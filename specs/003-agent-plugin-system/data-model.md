# Data Model: Agent Plugin System

**Feature Branch**: `003-agent-plugin-system`
**Date**: 2026-01-26

## Entities

### 1. AgentPlugin (Abstract Base)

Represents a plugin that provides tools for a specific Mythic agent type.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class ToolDefinition:
    """Definition of a single plugin tool."""
    name: str                      # Command name (without prefix), e.g., "shell"
    description: str               # Tool description for MCP schema
    parameters: type               # Pydantic model class for parameters
    handler: Callable[..., Any]    # Async function that executes the tool

@dataclass
class AgentPlugin(ABC):
    """Base class for agent plugins."""
    agent_name: str                # e.g., "apollo", "arachne"
    agent_description: str         # Human-readable description
    supported_os: list[str] = field(default_factory=list)  # e.g., ["Windows"]

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        """Return list of tools provided by this plugin."""
        pass

    def get_tool_name(self, command_name: str) -> str:
        """Get namespaced tool name."""
        return f"{self.agent_name}_{command_name}"
```

**Validation Rules**:
- `agent_name` must be lowercase alphanumeric (no spaces/special chars)
- `agent_name` must be unique across all loaded plugins
- Each tool's `name` must be unique within the plugin

**State Transitions**: N/A (stateless definition)

---

### 2. PluginRegistry

Singleton registry that manages all loaded plugins and their tools.

```python
@dataclass
class LoadedPlugin:
    """A successfully loaded plugin with its tools."""
    plugin: AgentPlugin
    tools: list[ToolDefinition]
    load_time_ms: float

@dataclass
class PluginLoadError:
    """Error encountered while loading a plugin."""
    plugin_path: str
    error_type: str
    error_message: str

class PluginRegistry:
    """Registry for managing loaded plugins."""

    _plugins: dict[str, LoadedPlugin]       # agent_name -> LoadedPlugin
    _tools: dict[str, ToolDefinition]       # full_tool_name -> ToolDefinition
    _load_errors: list[PluginLoadError]     # Errors for logging

    def register_plugin(self, plugin: AgentPlugin) -> None: ...
    def get_plugin(self, agent_name: str) -> AgentPlugin | None: ...
    def get_tool(self, tool_name: str) -> ToolDefinition | None: ...
    def get_all_tools(self) -> list[ToolDefinition]: ...
    def list_plugins(self) -> list[str]: ...
    def get_load_errors(self) -> list[PluginLoadError]: ...
```

**Validation Rules**:
- Plugin registration fails if `agent_name` already exists
- Tool registration fails if `tool_name` already exists (across all plugins)

---

### 3. TaskExecution (Request/Response)

Models for executing agent commands and returning results.

```python
from pydantic import BaseModel, Field
from enum import Enum

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
```

**Validation Rules**:
- `callback_id` must be positive integer
- `timeout` must be in range [30, 300] seconds
- `parameters` keys must match command's expected parameter names

---

### 4. AgentTypeValidation

Helper model for validating callback agent type matches plugin.

```python
class AgentTypeMismatchError(Exception):
    """Raised when callback's agent type doesn't match tool's required type."""
    def __init__(self, expected: str, actual: str, callback_id: int):
        self.expected = expected
        self.actual = actual
        self.callback_id = callback_id
        super().__init__(
            f"Agent type mismatch: tool requires '{expected}' but callback {callback_id} is '{actual}'"
        )

class CallbackAgentInfo(BaseModel):
    """Agent type information for a callback."""
    callback_id: int
    agent_type: str
    active: bool
```

---

### 5. PluginToolResponse (MCP Response Models)

Generic response models for plugin tools.

```python
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
```

---

## Relationships

```
PluginRegistry (1) --contains--> (N) LoadedPlugin
LoadedPlugin (1) --wraps--> (1) AgentPlugin
AgentPlugin (1) --defines--> (N) ToolDefinition

ExecuteTaskRequest --> [TaskExecutor] --> ExecuteTaskResponse
                                      --> PluginToolSuccessResponse | PluginToolErrorResponse
```

---

## Example Plugin Tool Parameter Models

### Apollo Shell Command

```python
class ApolloShellParams(BaseModel):
    """Parameters for apollo_shell tool."""
    callback_id: int = Field(..., description="Callback ID to execute on")
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")
```

### Apollo Download Command

```python
class ApolloDownloadParams(BaseModel):
    """Parameters for apollo_download tool."""
    callback_id: int = Field(..., description="Callback ID to execute on")
    path: str = Field(..., description="Path to file to download")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")
```

### Arachne Shell Command

```python
class ArachneShellParams(BaseModel):
    """Parameters for arachne_shell tool."""
    callback_id: int = Field(..., description="Callback ID to execute on")
    command: str = Field(..., description="Command to execute")
    timeout: int = Field(default=60, ge=30, le=300, description="Timeout in seconds")
```
