"""Plugin system for MythicMCP.

Provides agent-specific tools through a plugin architecture.
Plugins are discovered and loaded at server startup.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Coroutine

from mcp.server.fastmcp import Context, FastMCP

from mythicmcp.plugins.base import AgentPlugin, ToolDefinition
from mythicmcp.plugins.registry import LoadedPlugin, PluginLoadError, PluginRegistry

logger = logging.getLogger(__name__)

# Global plugin registry instance
_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    return _registry


def discover_builtin_plugins() -> list[Path]:
    """Discover builtin plugin modules in the plugins/builtin/ directory.

    Returns:
        List of paths to Python files that may contain plugins.
    """
    builtin_dir = Path(__file__).parent / "builtin"
    if not builtin_dir.exists():
        logger.warning(f"Builtin plugins directory not found: {builtin_dir}")
        return []

    plugin_files = []
    for path in builtin_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        plugin_files.append(path)

    logger.debug(f"Discovered {len(plugin_files)} builtin plugin files")
    return plugin_files


def discover_external_plugins(plugins_dir: str | None = None) -> list[Path]:
    """Discover external plugin modules from configured plugins directory.

    Args:
        plugins_dir: Path to external plugins directory. If None, uses
            MYTHICMCP_PLUGINS_DIR environment variable.

    Returns:
        List of paths to Python files that may contain plugins.
    """
    if plugins_dir is None:
        plugins_dir = os.environ.get("MYTHICMCP_PLUGINS_DIR")

    if not plugins_dir:
        return []

    plugins_path = Path(plugins_dir)
    if not plugins_path.exists():
        logger.warning(f"External plugins directory not found: {plugins_dir}")
        return []

    plugin_files = []
    for path in plugins_path.glob("*.py"):
        if path.name.startswith("_"):
            continue
        plugin_files.append(path)

    logger.debug(f"Discovered {len(plugin_files)} external plugin files from {plugins_dir}")
    return plugin_files


def load_plugin(plugin_path: Path) -> AgentPlugin | None:
    """Load a plugin from a Python file.

    Args:
        plugin_path: Path to the plugin Python file.

    Returns:
        Loaded AgentPlugin instance, or None if loading failed.

    The plugin file must contain a class that inherits from AgentPlugin.
    If multiple plugin classes are found, only the first is loaded.
    """
    module_name = f"mythicmcp.plugins.external.{plugin_path.stem}"

    try:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not load spec for plugin: {plugin_path}")
            _registry.add_load_error(PluginLoadError(
                plugin_path=str(plugin_path),
                error_type="import_error",
                error_message="Could not create module spec",
            ))
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find AgentPlugin subclass in module
        plugin_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, AgentPlugin)
                and obj is not AgentPlugin
            ):
                plugin_class = obj
                break

        if plugin_class is None:
            logger.warning(f"No AgentPlugin subclass found in: {plugin_path}")
            _registry.add_load_error(PluginLoadError(
                plugin_path=str(plugin_path),
                error_type="invalid_plugin",
                error_message="No AgentPlugin subclass found",
            ))
            return None

        # Instantiate the plugin
        plugin = plugin_class()
        logger.debug(f"Loaded plugin '{plugin.agent_name}' from {plugin_path}")
        return plugin

    except Exception as e:
        logger.warning(f"Failed to load plugin from {plugin_path}: {e}")
        _registry.add_load_error(PluginLoadError(
            plugin_path=str(plugin_path),
            error_type="load_error",
            error_message=str(e),
        ))
        return None


def _load_builtin_plugin_module(module_name: str) -> AgentPlugin | None:
    """Load a builtin plugin module by name.

    Args:
        module_name: Full module name (e.g., 'mythicmcp.plugins.builtin.apollo').

    Returns:
        Loaded AgentPlugin instance, or None if loading failed.
    """
    try:
        module = importlib.import_module(module_name)

        # Find AgentPlugin subclass in module
        plugin_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, AgentPlugin)
                and obj is not AgentPlugin
            ):
                plugin_class = obj
                break

        if plugin_class is None:
            logger.warning(f"No AgentPlugin subclass found in: {module_name}")
            _registry.add_load_error(PluginLoadError(
                plugin_path=module_name,
                error_type="invalid_plugin",
                error_message="No AgentPlugin subclass found",
            ))
            return None

        # Instantiate the plugin
        plugin = plugin_class()
        logger.debug(f"Loaded builtin plugin '{plugin.agent_name}'")
        return plugin

    except Exception as e:
        logger.warning(f"Failed to load builtin plugin {module_name}: {e}")
        _registry.add_load_error(PluginLoadError(
            plugin_path=module_name,
            error_type="load_error",
            error_message=str(e),
        ))
        return None


def load_all_plugins() -> PluginRegistry:
    """Load all available plugins (builtin and external).

    Returns:
        The populated PluginRegistry instance.
    """
    # Load builtin plugins by module import (more reliable than file discovery)
    builtin_modules = [
        "mythicmcp.plugins.builtin.apollo",
        "mythicmcp.plugins.builtin.arachne",
    ]

    for module_name in builtin_modules:
        start_time = time.perf_counter()
        plugin = _load_builtin_plugin_module(module_name)
        if plugin:
            load_time_ms = (time.perf_counter() - start_time) * 1000
            _registry.register_plugin(plugin, load_time_ms)
            logger.info(f"Registered plugin '{plugin.agent_name}' with {len(plugin.get_tools())} tools")

    # Load external plugins from configured directory
    external_paths = discover_external_plugins()
    for plugin_path in external_paths:
        start_time = time.perf_counter()
        plugin = load_plugin(plugin_path)
        if plugin:
            load_time_ms = (time.perf_counter() - start_time) * 1000
            _registry.register_plugin(plugin, load_time_ms)
            logger.info(f"Registered external plugin '{plugin.agent_name}' with {len(plugin.get_tools())} tools")

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
