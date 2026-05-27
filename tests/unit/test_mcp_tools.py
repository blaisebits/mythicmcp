"""Integration tests for MCP tool availability.

These tests verify that all expected MCP tools are properly registered
and available through the MythicMCP server.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def clear_tool_registration_env(monkeypatch: pytest.MonkeyPatch):
    """Keep default tool registration tests isolated from shell env state."""
    monkeypatch.delenv("MYTHIC_HOTLOAD", raising=False)
    monkeypatch.delenv("MYTHIC_DEV", raising=False)
    monkeypatch.delenv("MYTHIC_AGENTS", raising=False)


# Expected tools that MythicMCP should expose
EXPECTED_TOOLS = {
    "core_list_callbacks",
    "core_get_callback",
    "core_list_callback_commands",
    "core_get_callback_command",
    "core_execute_callback_command",
    "core_get_operation",
    "core_check_connection",
    "core_list_operations",
    "core_set_operation",
    "core_list_plugins",
    "core_upload_file",
    "core_download_file",
    "core_list_downloaded_files",
    "core_list_uploaded_files",
    "load_agent_tools",
    "unload_agent_tools",
    "list_available_agents",
    "core_list_c2_profiles",
    "core_get_c2_profile_parameters",
    "core_create_c2_instance",
    "core_list_c2_instances",
    "core_get_c2_instance",
    "core_delete_c2_instance",
}


class TestMCPToolRegistration:
    """Test MCP tool registration without starting the server."""

    def test_all_expected_tools_registered(self):
        """Verify all expected tools are registered with the MCP server."""
        from mythicmcp.server import mcp

        registered_tools = set(mcp._tool_manager._tools.keys())

        missing_tools = EXPECTED_TOOLS - registered_tools
        assert not missing_tools, f"Missing tools: {missing_tools}"

    def test_no_unexpected_tools_removed(self):
        """Verify expected tools haven't been accidentally removed."""
        from mythicmcp.server import mcp

        registered_tools = set(mcp._tool_manager._tools.keys())

        # All expected tools should be present
        for tool_name in EXPECTED_TOOLS:
            assert tool_name in registered_tools, f"Tool '{tool_name}' is missing"

    def test_tools_have_descriptions(self):
        """Verify all tools have descriptions for discoverability."""
        from mythicmcp.server import mcp

        for tool_name in EXPECTED_TOOLS:
            tool = mcp._tool_manager._tools.get(tool_name)
            assert tool is not None, f"Tool '{tool_name}' not found"
            assert tool.description, f"Tool '{tool_name}' has no description"
            assert len(tool.description) > 10, f"Tool '{tool_name}' has too short description"

    def test_core_list_callbacks_tool(self):
        """Verify core_list_callbacks tool is properly configured."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_callbacks")
        assert tool is not None
        assert "callback" in tool.description.lower()
        assert "list" in tool.description.lower()

    def test_core_get_callback_tool(self):
        """Verify core_get_callback tool is properly configured."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_get_callback")
        assert tool is not None
        assert "callback" in tool.description.lower()

    def test_execute_callback_command_description_mentions_json_arguments(self):
        """Generic execute docs should advertise JSON-object argument mode."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_execute_callback_command")
        assert tool is not None
        assert "json object string" in tool.description.lower()
        assert "argument_mode" in tool.description
        assert "execution_usage" in tool.description

    def test_core_get_operation_tool(self):
        """Verify core_get_operation tool is properly configured."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_get_operation")
        assert tool is not None
        assert "operation" in tool.description.lower()

    def test_core_check_connection_tool(self):
        """Verify core_check_connection tool is properly configured."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_check_connection")
        assert tool is not None
        assert "connection" in tool.description.lower() or "connectivity" in tool.description.lower()

    def test_dev_tools_hidden_by_default(self):
        """Development tools are not exposed unless MYTHIC_DEV is enabled."""
        from mythicmcp.server import mcp

        assert "dev_reload_runtime" not in mcp._tool_manager._tools

    def test_dev_tools_exposed_when_enabled(self, monkeypatch: pytest.MonkeyPatch):
        """Development tools are exposed when MYTHIC_DEV=true."""
        import mythicmcp.server as server_module

        monkeypatch.setenv("MYTHIC_DEV", "true")
        reloaded = importlib.reload(server_module)

        try:
            assert "dev_reload_runtime" in reloaded.mcp._tool_manager._tools
        finally:
            monkeypatch.delenv("MYTHIC_DEV", raising=False)
            importlib.reload(server_module)

    def test_hotload_tools_hidden_when_disabled(self, monkeypatch: pytest.MonkeyPatch):
        """Dynamic agent load/unload tools are hidden when MYTHIC_HOTLOAD=false."""
        import mythicmcp.server as server_module

        monkeypatch.setenv("MYTHIC_HOTLOAD", "false")
        reloaded = importlib.reload(server_module)

        try:
            assert "load_agent_tools" not in reloaded.mcp._tool_manager._tools
            assert "unload_agent_tools" not in reloaded.mcp._tool_manager._tools
        finally:
            monkeypatch.delenv("MYTHIC_HOTLOAD", raising=False)
            importlib.reload(server_module)

    def test_hotload_tools_hidden_when_disabled_with_zero(self, monkeypatch: pytest.MonkeyPatch):
        """Dynamic agent load/unload tools are hidden when MYTHIC_HOTLOAD=0."""
        import mythicmcp.server as server_module

        monkeypatch.setenv("MYTHIC_HOTLOAD", "0")
        reloaded = importlib.reload(server_module)

        try:
            assert "load_agent_tools" not in reloaded.mcp._tool_manager._tools
            assert "unload_agent_tools" not in reloaded.mcp._tool_manager._tools
        finally:
            monkeypatch.delenv("MYTHIC_HOTLOAD", raising=False)
            importlib.reload(server_module)

    def test_startup_agents_preloaded(self, monkeypatch: pytest.MonkeyPatch):
        """MYTHIC_AGENTS preloads selected agent tools during startup."""
        import mythicmcp.server as server_module
        from mythicmcp.plugins import get_registry

        monkeypatch.setenv("MYTHIC_AGENTS", "apollo")
        reloaded = importlib.reload(server_module)
        registry = get_registry()
        registry.clear()

        try:
            reloaded._load_plugins()
            assert registry.is_agent_registered("apollo")
            assert "apollo_shell" in reloaded.mcp._tool_manager._tools
        finally:
            registry.clear()
            monkeypatch.delenv("MYTHIC_AGENTS", raising=False)
            importlib.reload(server_module)

    def test_multiple_startup_agents_preloaded(self, monkeypatch: pytest.MonkeyPatch):
        """MYTHIC_AGENTS can preload multiple agent toolsets."""
        import mythicmcp.server as server_module
        from mythicmcp.plugins import get_registry

        monkeypatch.setenv("MYTHIC_AGENTS", "apollo,poseidon")
        reloaded = importlib.reload(server_module)
        registry = get_registry()
        registry.clear()

        try:
            reloaded._load_plugins()
            assert registry.is_agent_registered("apollo")
            assert registry.is_agent_registered("poseidon")
            assert "apollo_shell" in reloaded.mcp._tool_manager._tools
            assert "poseidon_shell" in reloaded.mcp._tool_manager._tools
        finally:
            registry.clear()
            monkeypatch.delenv("MYTHIC_AGENTS", raising=False)
            importlib.reload(server_module)

    def test_all_startup_agents_preloaded(self, monkeypatch: pytest.MonkeyPatch):
        """MYTHIC_AGENTS=all preloads every discovered agent."""
        import mythicmcp.server as server_module
        from mythicmcp.plugins import get_registry

        monkeypatch.setenv("MYTHIC_AGENTS", "all")
        reloaded = importlib.reload(server_module)
        registry = get_registry()
        registry.clear()

        try:
            reloaded._load_plugins()
            assert registry.is_agent_registered("apollo")
            assert registry.is_agent_registered("arachne")
            assert registry.is_agent_registered("poseidon")
            assert "apollo_shell" in reloaded.mcp._tool_manager._tools
            assert "arachne_shell" in reloaded.mcp._tool_manager._tools
            assert "poseidon_shell" in reloaded.mcp._tool_manager._tools
        finally:
            registry.clear()
            monkeypatch.delenv("MYTHIC_AGENTS", raising=False)
            importlib.reload(server_module)


class TestMCPServerConfiguration:
    """Test MCP server configuration."""

    def test_server_has_name(self):
        """Verify the MCP server has a proper name."""
        from mythicmcp.server import mcp

        assert mcp.name == "MythicMCP"

    def test_server_has_mcp_server(self):
        """Verify the MCP server is properly initialized."""
        from mythicmcp.server import mcp

        # The FastMCP wrapper should have an internal MCP server
        assert mcp._mcp_server is not None

    @pytest.mark.asyncio
    async def test_usage_patterns_resource_registered_and_readable(self):
        """The usage-patterns resource should be exposed for agents to read."""
        from mythicmcp.server import mcp

        resources = await mcp.list_resources()
        uris = {str(resource.uri) for resource in resources}

        assert "mythic://docs/usage-patterns" in uris

        content = await mcp.read_resource("mythic://docs/usage-patterns")
        text = content[0].content
        assert "core_set_operation" in text
        assert "core_list_callback_commands" in text
        assert "core_get_callback_command" in text
        assert "core_execute_callback_command" in text
        assert "task output" in text.lower()
        assert "json object string" in text.lower()
