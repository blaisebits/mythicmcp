"""Plugin system for MythicMCP.

Provides agent-specific tools through a plugin architecture.
Plugins are discovered and loaded at server startup.
"""

from __future__ import annotations

import inspect
import keyword
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Coroutine

from makefun import create_function
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


def reload_all_plugins(mcp: FastMCP | None = None) -> tuple[list[str], int]:
    """Reload YAML plugins and restore any currently-registered agent tools.

    Args:
        mcp: Optional FastMCP server instance. If provided, agent tools that are
            currently registered with MCP are removed before reload, then
            re-registered from the fresh plugin definitions.

    Returns:
        Tuple of:
        - agent names restored into the MCP tool list
        - total number of tool handlers re-registered
    """
    previously_registered = list(_registry.list_registered_agents())

    if mcp is not None:
        for agent_name in previously_registered:
            try:
                unregister_agent_from_mcp(mcp, agent_name)
            except Exception:
                logger.warning(
                    "Failed to unload agent '%s' during plugin reload",
                    agent_name,
                    exc_info=True,
                )

    _registry.clear()
    load_all_plugins()

    restored_agents: list[str] = []
    restored_tool_count = 0

    if mcp is not None:
        for agent_name in previously_registered:
            if _registry.get_loaded_plugin(agent_name) is None:
                logger.warning(
                    "Agent '%s' disappeared during reload; skipping restore",
                    agent_name,
                )
                continue

            tool_names = register_agent_with_mcp(mcp, agent_name)
            restored_agents.append(agent_name)
            restored_tool_count += len(tool_names)

    return restored_agents, restored_tool_count


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
    param_name_map: dict[str, str] = {}

    def to_safe_param_name(field_name: str) -> str:
        safe_name = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in field_name)
        if not safe_name:
            safe_name = "field"
        if safe_name[0].isdigit():
            safe_name = f"field_{safe_name}"
        if keyword.iskeyword(safe_name):
            safe_name = f"{safe_name}_"

        candidate = safe_name
        counter = 2
        while candidate in param_name_map:
            candidate = f"{safe_name}_{counter}"
            counter += 1
        return candidate

    async def tool_handler_impl(ctx: Context, **kwargs: Any) -> Any:
        """Generated tool handler that delegates to plugin handler."""
        params = tool_def.parameters(
            **{param_name_map.get(name, name): value for name, value in kwargs.items()}
        )
        return await tool_def.handler(ctx, params)

    parameters = [
        inspect.Parameter(
            "ctx",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Context,
        )
    ]
    for field_name, field_info in tool_def.parameters.model_fields.items():
        safe_name = to_safe_param_name(field_name)
        param_name_map[safe_name] = field_name
        default = inspect.Parameter.empty if field_info.is_required() else field_info.default
        annotation = field_info.annotation if field_info.annotation is not None else Any
        parameters.append(
            inspect.Parameter(
                safe_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=annotation,
                default=default,
            )
        )

    signature = inspect.Signature(parameters=parameters, return_annotation=Any)
    return create_function(
        signature,
        tool_handler_impl,
        func_name=full_tool_name,
        doc=tool_def.description,
        module_name=__name__,
    )


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


def register_agent_with_mcp(mcp: FastMCP, agent_name: str) -> list[str]:
    """Dynamically register all tools for a specific agent with FastMCP.

    Args:
        mcp: FastMCP server instance.
        agent_name: Name of the agent whose tools to register.

    Returns:
        List of tool names that were registered.

    Raises:
        AgentNotFoundError: If agent not found in registry.
        AgentAlreadyLoadedError: If agent tools are already registered.
    """
    from mythicmcp.plugins.errors import AgentAlreadyLoadedError, AgentNotFoundError

    loaded = _registry.get_loaded_plugin(agent_name)
    if loaded is None:
        raise AgentNotFoundError(f"Agent '{agent_name}' not found in plugin registry")

    if _registry.is_agent_registered(agent_name):
        raise AgentAlreadyLoadedError(f"Agent '{agent_name}' tools are already loaded")

    registered_names = []
    for tool_def in loaded.tools:
        handler = generate_tool_function(tool_def, agent_name)
        full_name = loaded.plugin.get_tool_name(tool_def.name)
        mcp.add_tool(handler, name=full_name, description=tool_def.description)
        registered_names.append(full_name)
        logger.debug(f"Dynamically registered tool: {full_name}")

    _registry.mark_agent_registered(agent_name)
    logger.info(
        f"Dynamically registered {len(registered_names)} tools for agent '{agent_name}'"
    )
    return registered_names


def unregister_agent_from_mcp(mcp: FastMCP, agent_name: str) -> int:
    """Dynamically remove all tools for a specific agent from FastMCP.

    Args:
        mcp: FastMCP server instance.
        agent_name: Name of the agent whose tools to remove.

    Returns:
        Number of tools that were removed.

    Raises:
        AgentNotFoundError: If agent not found in registry.
        AgentNotLoadedError: If agent tools are not currently registered.
    """
    from mythicmcp.plugins.errors import AgentNotFoundError, AgentNotLoadedError

    loaded = _registry.get_loaded_plugin(agent_name)
    if loaded is None:
        raise AgentNotFoundError(f"Agent '{agent_name}' not found in plugin registry")

    if not _registry.is_agent_registered(agent_name):
        raise AgentNotLoadedError(f"Agent '{agent_name}' tools are not currently loaded")

    removed_count = 0
    for tool_def in loaded.tools:
        full_name = loaded.plugin.get_tool_name(tool_def.name)
        try:
            mcp.remove_tool(full_name)
            removed_count += 1
            logger.debug(f"Dynamically removed tool: {full_name}")
        except Exception:
            logger.warning(f"Failed to remove tool: {full_name}")

    # Only mark unregistered if all tools were successfully removed
    if removed_count == len(loaded.tools):
        _registry.mark_agent_unregistered(agent_name)
    else:
        logger.warning(
            f"Partial unload for '{agent_name}': {removed_count}/{len(loaded.tools)} "
            f"tools removed, agent still marked as registered"
        )

    logger.info(
        f"Dynamically removed {removed_count} tools for agent '{agent_name}'"
    )
    return removed_count


__all__ = [
    "AgentPlugin",
    "ToolDefinition",
    "PluginRegistry",
    "LoadedPlugin",
    "PluginLoadError",
    "get_registry",
    "load_all_plugins",
    "reload_all_plugins",
    "register_plugin_tools",
    "register_agent_with_mcp",
    "unregister_agent_from_mcp",
]
