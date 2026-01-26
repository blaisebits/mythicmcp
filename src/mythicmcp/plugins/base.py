"""Base classes for MythicMCP agent plugins.

Provides abstract base class and data structures for implementing
agent-specific plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Coroutine

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context
    from pydantic import BaseModel


@dataclass
class ToolDefinition:
    """Definition of a single plugin tool.

    Attributes:
        name: Command name without agent prefix (e.g., "shell", "download").
        description: Tool description for MCP schema.
        parameters: Pydantic model class for tool parameters.
        handler: Async function that executes the tool.
    """

    name: str
    description: str
    parameters: type[BaseModel]
    handler: Callable[[Context, Any], Coroutine[Any, Any, Any]]


@dataclass
class AgentPlugin(ABC):
    """Abstract base class for agent plugins.

    Plugins provide agent-specific tools for executing commands on
    Mythic callbacks. Each plugin targets a specific agent type
    (e.g., Apollo, Arachne).

    Attributes:
        agent_name: Lowercase agent identifier (e.g., "apollo", "arachne").
        agent_description: Human-readable description of the agent.
        supported_os: List of supported operating systems.
    """

    agent_name: str = ""
    agent_description: str = ""
    supported_os: list[str] = field(default_factory=list)

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        """Return list of tools provided by this plugin.

        Returns:
            List of ToolDefinition objects describing each tool.
        """
        pass

    def get_tool_name(self, command_name: str) -> str:
        """Get namespaced tool name with agent prefix.

        Args:
            command_name: The command name without prefix.

        Returns:
            Full tool name with agent prefix (e.g., "apollo_shell").
        """
        return f"{self.agent_name}_{command_name}"
