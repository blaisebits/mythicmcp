"""Tests for dynamic agent tool loading/unloading."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from mythicmcp.plugins import (
    get_registry,
    reload_all_plugins,
    register_agent_with_mcp,
    unregister_agent_from_mcp,
)
from mythicmcp.plugins.registry import PluginRegistry
from mythicmcp.models import (
    AgentToolsErrorResponse,
    AvailableAgentInfo,
    DevReloadResponse,
    ListAvailableAgentsResponse,
    LoadAgentToolsResponse,
    UnloadAgentToolsResponse,
)
from mythicmcp.plugins.errors import (
    AgentAlreadyLoadedError,
    AgentNotFoundError,
    AgentNotLoadedError,
)


@pytest.fixture
def fresh_registry():
    """Provide a clean registry and restore after test."""
    registry = get_registry()
    registry.clear()
    yield registry
    registry.clear()


@pytest.fixture
def mcp_server():
    """Create a fresh FastMCP server for testing."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("test-dynamic-loading")


@pytest.fixture
def loaded_registry(fresh_registry):
    """Registry with builtin plugins loaded."""
    from mythicmcp.plugins import load_all_plugins
    # Clear and reload
    fresh_registry.clear()
    load_all_plugins()
    return fresh_registry


class TestRegistryTracking:
    """Tests for PluginRegistry registration tracking."""

    def test_initial_state_no_registered_agents(self, fresh_registry):
        assert fresh_registry.list_registered_agents() == []

    def test_mark_agent_registered(self, fresh_registry):
        fresh_registry.mark_agent_registered("apollo")
        assert fresh_registry.is_agent_registered("apollo")
        assert "apollo" in fresh_registry.list_registered_agents()

    def test_mark_agent_unregistered(self, fresh_registry):
        fresh_registry.mark_agent_registered("apollo")
        fresh_registry.mark_agent_unregistered("apollo")
        assert not fresh_registry.is_agent_registered("apollo")

    def test_unregister_nonexistent_is_safe(self, fresh_registry):
        # discard on set doesn't raise
        fresh_registry.mark_agent_unregistered("nonexistent")
        assert not fresh_registry.is_agent_registered("nonexistent")

    def test_clear_clears_registered_agents(self, fresh_registry):
        fresh_registry.mark_agent_registered("apollo")
        fresh_registry.mark_agent_registered("poseidon")
        fresh_registry.clear()
        assert fresh_registry.list_registered_agents() == []


class TestDynamicRegistration:
    """Tests for register_agent_with_mcp / unregister_agent_from_mcp."""

    def test_load_agent_registers_tools(self, loaded_registry, mcp_server):
        names = register_agent_with_mcp(mcp_server, "arachne")
        assert len(names) == 8
        assert "arachne_shell" in names
        assert loaded_registry.is_agent_registered("arachne")

        # Verify tools appear in MCP
        tools = asyncio.run(mcp_server.list_tools())
        tool_names = [t.name for t in tools]
        assert "arachne_shell" in tool_names

    def test_load_agent_not_found_raises(self, loaded_registry, mcp_server):
        with pytest.raises(AgentNotFoundError, match="not found"):
            register_agent_with_mcp(mcp_server, "nonexistent")

    def test_load_agent_already_loaded_raises(self, loaded_registry, mcp_server):
        register_agent_with_mcp(mcp_server, "arachne")
        with pytest.raises(AgentAlreadyLoadedError, match="already loaded"):
            register_agent_with_mcp(mcp_server, "arachne")

    def test_unload_agent_removes_tools(self, loaded_registry, mcp_server):
        register_agent_with_mcp(mcp_server, "arachne")
        removed = unregister_agent_from_mcp(mcp_server, "arachne")
        assert removed == 8
        assert not loaded_registry.is_agent_registered("arachne")

        # Verify tools gone from MCP
        tools = asyncio.run(mcp_server.list_tools())
        tool_names = [t.name for t in tools]
        assert "arachne_shell" not in tool_names

    def test_unload_agent_not_loaded_raises(self, loaded_registry, mcp_server):
        with pytest.raises(AgentNotLoadedError, match="not currently loaded"):
            unregister_agent_from_mcp(mcp_server, "arachne")

    def test_unload_agent_not_found_raises(self, loaded_registry, mcp_server):
        with pytest.raises(AgentNotFoundError, match="not found"):
            unregister_agent_from_mcp(mcp_server, "nonexistent")

    def test_load_unload_cycle(self, loaded_registry, mcp_server):
        """Load, unload, re-load should work cleanly."""
        register_agent_with_mcp(mcp_server, "arachne")
        assert loaded_registry.is_agent_registered("arachne")

        unregister_agent_from_mcp(mcp_server, "arachne")
        assert not loaded_registry.is_agent_registered("arachne")

        # Re-load should work
        names = register_agent_with_mcp(mcp_server, "arachne")
        assert len(names) == 8
        assert loaded_registry.is_agent_registered("arachne")

    def test_multiple_agents_independent(self, loaded_registry, mcp_server):
        """Loading/unloading one agent doesn't affect others."""
        register_agent_with_mcp(mcp_server, "apollo")
        register_agent_with_mcp(mcp_server, "arachne")

        unregister_agent_from_mcp(mcp_server, "apollo")
        assert not loaded_registry.is_agent_registered("apollo")
        assert loaded_registry.is_agent_registered("arachne")

        tools = asyncio.run(mcp_server.list_tools())
        tool_names = [t.name for t in tools]
        assert "arachne_shell" in tool_names
        assert "apollo_shell" not in tool_names

    def test_reload_all_plugins_restores_registered_agents(self, loaded_registry, mcp_server):
        register_agent_with_mcp(mcp_server, "apollo")

        restored_agents, restored_tool_count = reload_all_plugins(mcp_server)

        assert restored_agents == ["apollo"]
        assert restored_tool_count > 0
        assert loaded_registry.is_agent_registered("apollo")

        tools = asyncio.run(mcp_server.list_tools())
        tool_names = [t.name for t in tools]
        assert "apollo_shell" in tool_names

    def test_generated_tool_schema_uses_flat_parameters(self, loaded_registry, mcp_server):
        register_agent_with_mcp(mcp_server, "apollo")

        tool = mcp_server._tool_manager.get_tool("apollo_shell")
        assert tool is not None
        properties = tool.parameters.get("properties", {})

        assert "callback_id" in properties
        assert "command" in properties
        assert "kwargs" not in properties

    def test_generated_tool_accepts_flat_args(self, loaded_registry, mcp_server, monkeypatch):
        captured: dict = {}

        async def fake_execute_with_validation(**kwargs):
            captured.update(kwargs)
            return {"status": "ok"}

        monkeypatch.setattr(
            "mythicmcp.plugins.executor.execute_with_validation",
            fake_execute_with_validation,
        )

        register_agent_with_mcp(mcp_server, "apollo")

        result = asyncio.run(
            mcp_server._tool_manager.call_tool(
                "apollo_shell",
                {"callback_id": 5, "command": "whoami"},
            )
        )

        assert result == {"status": "ok"}
        assert captured["callback_id"] == 5
        assert captured["command_name"] == "shell"
        assert captured["parameters"] == "whoami"

    def test_generated_tool_keeps_dict_params_for_non_raw_commands(
        self,
        loaded_registry,
        mcp_server,
        monkeypatch,
    ):
        captured: dict = {}

        async def fake_execute_with_validation(**kwargs):
            captured.update(kwargs)
            return {"status": "ok"}

        monkeypatch.setattr(
            "mythicmcp.plugins.executor.execute_with_validation",
            fake_execute_with_validation,
        )

        register_agent_with_mcp(mcp_server, "apollo")

        result = asyncio.run(
            mcp_server._tool_manager.call_tool(
                "apollo_run",
                {"callback_id": 5, "executable": "whoami.exe", "arguments": ""},
            )
        )

        assert result == {"status": "ok"}
        assert captured["command_name"] == "run"
        assert captured["parameters"] == {"executable": "whoami.exe", "arguments": ""}

    def test_generated_tool_missing_arg_reports_real_field(self, loaded_registry, mcp_server):
        register_agent_with_mcp(mcp_server, "apollo")

        with pytest.raises(ToolError) as excinfo:
            asyncio.run(
                mcp_server._tool_manager.call_tool(
                    "apollo_shell",
                    {"command": "whoami"},
                )
            )

        assert "callback_id" in str(excinfo.value)
        assert "kwargs" not in str(excinfo.value)


class TestStartupBehavior:
    """Tests for startup agent registration behavior."""

    def test_no_agent_tools_after_load_plugins(self, fresh_registry):
        """_load_plugins should leave agent tools unloaded by default."""
        from mythicmcp.server import _load_plugins

        fresh_registry.clear()
        _load_plugins()

        # Plugins are in registry but NOT registered with MCP
        assert len(fresh_registry.list_plugins()) == 3
        assert len(fresh_registry.list_registered_agents()) == 0

    def test_startup_agents_register_when_configured(
        self,
        fresh_registry,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """_load_plugins preloads configured startup agents."""
        import importlib

        import mythicmcp.server as server_module

        monkeypatch.setenv("MYTHIC_AGENTS", "arachne")
        reloaded = importlib.reload(server_module)
        fresh_registry.clear()

        try:
            reloaded._load_plugins()
            assert fresh_registry.is_agent_registered("arachne")
            assert "arachne_shell" in reloaded.mcp._tool_manager._tools
        finally:
            fresh_registry.clear()
            monkeypatch.delenv("MYTHIC_AGENTS", raising=False)
            importlib.reload(server_module)


class TestResponseModels:
    """Tests for Pydantic response models."""

    def test_load_response_model(self):
        resp = LoadAgentToolsResponse(
            agent_name="apollo",
            tools_loaded=78,
            tool_names=["apollo_shell"],
        )
        assert resp.success is True
        assert resp.agent_name == "apollo"
        assert resp.tools_loaded == 78

    def test_error_response_model_not_found(self):
        resp = AgentToolsErrorResponse(
            error="Agent 'foo' not found",
            error_type="not_found",
            agent_name="foo",
        )
        assert resp.success is False
        assert resp.error_type == "not_found"

    def test_error_response_model_not_loaded(self):
        resp = AgentToolsErrorResponse(
            error="Not loaded",
            error_type="not_loaded",
            agent_name="apollo",
        )
        assert resp.success is False
        assert resp.error_type == "not_loaded"

    def test_unload_response_model(self):
        resp = UnloadAgentToolsResponse(
            agent_name="apollo",
            tools_removed=78,
        )
        assert resp.success is True
        assert resp.tools_removed == 78

    def test_available_agent_info_model(self):
        info = AvailableAgentInfo(
            agent_name="apollo",
            agent_description="Windows C# agent",
            tool_count=78,
            supported_os=["Windows"],
            loaded=False,
        )
        assert info.loaded is False

    def test_list_available_agents_response(self):
        resp = ListAvailableAgentsResponse(
            agents=[],
            total_count=0,
            loaded_count=0,
        )
        assert resp.total_count == 0
        assert resp.retrieved_at is not None

    def test_dev_reload_response_model(self):
        resp = DevReloadResponse(
            modules_reloaded=["mythicmcp.tools.status"],
            module_count=1,
            reloaded_agents=["apollo"],
            reloaded_tool_count=3,
            available_agents=3,
        )
        assert resp.success is True
        assert resp.module_count == 1
        assert resp.reloaded_agents == ["apollo"]
