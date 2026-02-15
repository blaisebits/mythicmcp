"""Plugin system for MythicMCP.

Provides agent-specific tools through a plugin architecture.
Plugins are discovered and loaded at server startup.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Coroutine

from mcp.server.fastmcp import Context, FastMCP

from mythicmcp.plugins.base import AgentPlugin, ToolDefinition
from mythicmcp.plugins.registry import LoadedPlugin, PluginLoadError, PluginRegistry
from mythicmcp.plugins.yaml_loader import (
    YamlConfigError,
    discover_yaml_configs,
    load_yaml_plugin,
)

logger = logging.getLogger(__name__)

# Global plugin registry instance
_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    return _registry


def _load_yaml_configs_from_dir(directory: Path) -> None:
    """Discover and load YAML config files from a directory.

    Args:
        directory: Directory to search for YAML config files.
    """
    yaml_paths = discover_yaml_configs(directory)
    for yaml_path in yaml_paths:
        start_time = time.perf_counter()
        result = load_yaml_plugin(yaml_path)
        if isinstance(result, YamlConfigError):
            logger.warning(str(result))
            _registry.add_load_error(PluginLoadError(
                plugin_path=str(yaml_path),
                error_type="validation_error",
                error_message=str(result),
            ))
            continue

        plugin = result
        load_time_ms = (time.perf_counter() - start_time) * 1000
        if _registry.register_plugin(plugin, load_time_ms):
            logger.info(
                f"Registered YAML plugin '{plugin.agent_name}' "
                f"with {len(plugin.get_tools())} tools from {yaml_path.name}"
            )


def load_all_plugins() -> PluginRegistry:
    """Load all available YAML plugins (builtin and external).

    Returns:
        The populated PluginRegistry instance.
    """
    # Load YAML configs from builtin directory
    builtin_dir = Path(__file__).parent / "builtin"
    _load_yaml_configs_from_dir(builtin_dir)

    # Load YAML configs from external directory
    external_dir = os.environ.get("MYTHICMCP_PLUGINS_DIR")
    if external_dir:
        external_path = Path(external_dir)
        _load_yaml_configs_from_dir(external_path)

    return _registry


def generate_tool_function(
    tool_def: ToolDefinition,
    agent_name: str,
) -> Callable[[Context, Any], Coroutine[Any, Any, Any]]:
    """Generate an MCP-compatible async tool handler function.

    Args:
        tool_def: Tool definition from the plugin.
        agent_name: Name of the agent this tool belongs to.

    Returns:
        Async function that can be registered with FastMCP.
    """
    full_tool_name = f"{agent_name}_{tool_def.name}"

    async def tool_handler(ctx: Context, **kwargs: Any) -> Any:
        """Generated tool handler that delegates to plugin handler."""
        # Create params model from kwargs
        params = tool_def.parameters(**kwargs)
        return await tool_def.handler(ctx, params)

    # Set function metadata for MCP schema
    tool_handler.__name__ = full_tool_name
    tool_handler.__doc__ = tool_def.description

    # Build parameter annotations for FastMCP schema generation
    annotations = {"ctx": Context, "return": Any}
    for field_name, field_info in tool_def.parameters.model_fields.items():
        annotations[field_name] = field_info.annotation

    tool_handler.__annotations__ = annotations

    return tool_handler


def register_plugin_tools(mcp: FastMCP) -> None:
    """Register all plugin tools with the FastMCP server.

    Args:
        mcp: FastMCP server instance.
    """
    for tool_name, (tool_def, agent_name) in _registry.get_all_tools().items():
        handler = generate_tool_function(tool_def, agent_name)
        mcp.tool()(handler)
        logger.debug(f"Registered tool: {tool_name}")

    total_tools = len(_registry.get_all_tools())
    logger.info(f"Registered {total_tools} plugin tools with MCP server")


__all__ = [
    "AgentPlugin",
    "ToolDefinition",
    "PluginRegistry",
    "LoadedPlugin",
    "PluginLoadError",
    "get_registry",
    "load_all_plugins",
    "register_plugin_tools",
]
