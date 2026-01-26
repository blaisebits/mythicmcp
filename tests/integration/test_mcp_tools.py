"""Integration tests for MCP tool availability.

These tests verify that all expected MCP tools are properly registered
and available through the MythicMCP server.
"""

from __future__ import annotations

import pytest


# Expected tools that MythicMCP should expose
EXPECTED_TOOLS = {
    "core_list_callbacks",
    "core_get_callback",
    "core_get_operation",
    "core_check_connection",
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
