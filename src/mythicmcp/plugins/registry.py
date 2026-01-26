"""Plugin registry for MythicMCP.

Manages loaded plugins and their tools, providing lookup and listing operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mythicmcp.plugins.base import AgentPlugin, ToolDefinition

logger = logging.getLogger(__name__)


@dataclass
class LoadedPlugin:
    """A successfully loaded plugin with its tools.

    Attributes:
        plugin: The loaded AgentPlugin instance.
        tools: List of tool definitions from the plugin.
        load_time_ms: Time taken to load the plugin in milliseconds.
    """

    plugin: AgentPlugin
    tools: list[ToolDefinition]
    load_time_ms: float


@dataclass
class PluginLoadError:
    """Error encountered while loading a plugin.

    Attributes:
        plugin_path: Path or module name that failed to load.
        error_type: Category of error (e.g., "import_error", "invalid_plugin").
        error_message: Human-readable error message.
    """

    plugin_path: str
    error_type: str
    error_message: str


@dataclass
class PluginRegistry:
    """Registry for managing loaded plugins.

    Provides methods for registering plugins, looking up tools,
    and listing available plugins.
    """

    _plugins: dict[str, LoadedPlugin] = field(default_factory=dict)
    _tools: dict[str, tuple[ToolDefinition, str]] = field(default_factory=dict)
    _load_errors: list[PluginLoadError] = field(default_factory=list)

    def register_plugin(self, plugin: AgentPlugin, load_time_ms: float = 0.0) -> bool:
        """Register a plugin with the registry.

        Args:
            plugin: The AgentPlugin instance to register.
            load_time_ms: Time taken to load the plugin.

        Returns:
            True if registration succeeded, False if agent_name already exists.
        """
        agent_name = plugin.agent_name

        if agent_name in self._plugins:
            logger.warning(
                f"Plugin name collision: '{agent_name}' is already registered. "
                f"Skipping duplicate plugin."
            )
            return False

        tools = plugin.get_tools()
        loaded = LoadedPlugin(plugin=plugin, tools=tools, load_time_ms=load_time_ms)
        self._plugins[agent_name] = loaded

        # Register all tools with namespaced names
        for tool in tools:
            full_name = plugin.get_tool_name(tool.name)
            if full_name in self._tools:
                logger.warning(
                    f"Tool name collision: '{full_name}' is already registered. "
                    f"Skipping duplicate tool."
                )
                continue
            self._tools[full_name] = (tool, agent_name)

        return True

    def get_plugin(self, agent_name: str) -> AgentPlugin | None:
        """Get a plugin by agent name.

        Args:
            agent_name: The agent name to look up.

        Returns:
            The AgentPlugin instance, or None if not found.
        """
        loaded = self._plugins.get(agent_name)
        return loaded.plugin if loaded else None

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        """Get a tool definition by full tool name.

        Args:
            tool_name: Full tool name including agent prefix (e.g., "apollo_shell").

        Returns:
            The ToolDefinition, or None if not found.
        """
        result = self._tools.get(tool_name)
        return result[0] if result else None

    def get_tool_with_agent(self, tool_name: str) -> tuple[ToolDefinition, str] | None:
        """Get a tool definition along with its agent name.

        Args:
            tool_name: Full tool name including agent prefix.

        Returns:
            Tuple of (ToolDefinition, agent_name), or None if not found.
        """
        return self._tools.get(tool_name)

    def get_all_tools(self) -> dict[str, tuple[ToolDefinition, str]]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to (ToolDefinition, agent_name) tuples.
        """
        return self._tools.copy()

    def list_plugins(self) -> list[str]:
        """List all registered plugin names.

        Returns:
            List of agent names for all registered plugins.
        """
        return list(self._plugins.keys())

    def get_loaded_plugin(self, agent_name: str) -> LoadedPlugin | None:
        """Get full loaded plugin info including load time.

        Args:
            agent_name: The agent name to look up.

        Returns:
            The LoadedPlugin info, or None if not found.
        """
        return self._plugins.get(agent_name)

    def add_load_error(self, error: PluginLoadError) -> None:
        """Record a plugin load error.

        Args:
            error: The PluginLoadError to record.
        """
        self._load_errors.append(error)

    def get_load_errors(self) -> list[PluginLoadError]:
        """Get all recorded load errors.

        Returns:
            List of PluginLoadError objects.
        """
        return self._load_errors.copy()

    def clear(self) -> None:
        """Clear all registered plugins and errors."""
        self._plugins.clear()
        self._tools.clear()
        self._load_errors.clear()
