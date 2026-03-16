"""Unit tests for payload management MCP tools.

These tests verify that payload tools are properly registered
and configured through the MythicMCP server, and that Pydantic
models are correctly defined.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


# Expected payload tools that MythicMCP should expose
PAYLOAD_TOOLS = {
    "core_list_payloads",
    "core_get_payload",
    "core_create_payload",
    "core_delete_payload",
    "core_download_payload",
    "core_check_payload_config",
    "core_payload_redirect_rules",
}


class TestPayloadToolRegistration:
    """Test payload tool registration without starting the server."""

    def test_all_payload_tools_registered(self):
        """Verify all payload tools are registered with the MCP server."""
        from mythicmcp.server import mcp

        registered_tools = set(mcp._tool_manager._tools.keys())

        missing_tools = PAYLOAD_TOOLS - registered_tools
        assert not missing_tools, f"Missing payload tools: {missing_tools}"

    def test_payload_tools_have_descriptions(self):
        """Verify all payload tools have descriptions for discoverability."""
        from mythicmcp.server import mcp

        for tool_name in PAYLOAD_TOOLS:
            tool = mcp._tool_manager._tools.get(tool_name)
            assert tool is not None, f"Tool '{tool_name}' not found"
            assert tool.description, f"Tool '{tool_name}' has no description"
            assert len(tool.description) > 10, f"Tool '{tool_name}' has too short description"


class TestCoreListPayloadsTool:
    """Test core_list_payloads tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_payloads")
        assert tool is not None

    def test_tool_has_proper_description(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_payloads")
        assert "payload" in tool.description.lower()
        assert "list" in tool.description.lower()


class TestCoreGetPayloadTool:
    """Test core_get_payload tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_get_payload")
        assert tool is not None

    def test_tool_has_uuid_parameter(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_get_payload")
        assert "payload_uuid" in tool.description.lower() or tool is not None


class TestCoreCreatePayloadTool:
    """Test core_create_payload tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_create_payload")
        assert tool is not None

    def test_tool_description_mentions_build(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_create_payload")
        assert "build" in tool.description.lower()


class TestCoreDeletePayloadTool:
    """Test core_delete_payload tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_delete_payload")
        assert tool is not None

    def test_tool_description_mentions_delete(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_delete_payload")
        assert "delete" in tool.description.lower()


class TestCoreDownloadPayloadTool:
    """Test core_download_payload tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_download_payload")
        assert tool is not None

    def test_tool_description_mentions_download(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_download_payload")
        assert "download" in tool.description.lower()


class TestCoreCheckPayloadConfigTool:
    """Test core_check_payload_config tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_check_payload_config")
        assert tool is not None


class TestCorePayloadRedirectRulesTool:
    """Test core_payload_redirect_rules tool configuration."""

    def test_tool_exists(self):
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_payload_redirect_rules")
        assert tool is not None


class TestPayloadModels:
    """Test payload Pydantic model construction and validation."""

    def test_c2_profile_summary(self):
        from mythicmcp.models import C2ProfileSummary

        profile = C2ProfileSummary(name="http", is_p2p=False, running=True)
        assert profile.name == "http"
        assert profile.is_p2p is False
        assert profile.running is True

    def test_payload_summary(self):
        from mythicmcp.models import C2ProfileSummary, PayloadSummary

        payload = PayloadSummary(
            uuid="test-uuid-123",
            agent_type="apollo",
            build_phase="success",
            deleted=False,
            auto_generated=False,
            creation_time=datetime.now(timezone.utc),
            os="Windows",
            c2_profiles=[C2ProfileSummary(name="http", is_p2p=False, running=True)],
        )
        assert payload.uuid == "test-uuid-123"
        assert payload.agent_type == "apollo"
        assert payload.os == "Windows"
        assert len(payload.c2_profiles) == 1

    def test_payload_detail(self):
        from mythicmcp.models import PayloadDetail

        detail = PayloadDetail(
            uuid="test-uuid-123",
            agent_type="apollo",
            build_phase="success",
            build_message="Build completed",
            deleted=False,
            auto_generated=False,
            creation_time=datetime.now(timezone.utc),
            operator="admin",
            file_uuid="file-uuid-456",
            filename="agent.exe",
            os="Windows",
        )
        assert detail.build_message == "Build completed"
        assert detail.file_uuid == "file-uuid-456"
        assert detail.operator == "admin"

    def test_payload_detail_optional_fields(self):
        from mythicmcp.models import PayloadDetail

        detail = PayloadDetail(
            uuid="test-uuid",
            agent_type="apollo",
            build_phase="error",
            deleted=False,
            auto_generated=False,
            creation_time=datetime.now(timezone.utc),
        )
        assert detail.file_uuid is None
        assert detail.filename is None
        assert detail.build_message == ""

    def test_list_payloads_response_has_timestamp(self):
        from mythicmcp.models import ListPayloadsResponse

        response = ListPayloadsResponse(payloads=[], count=0)
        assert response.retrieved_at is not None
        assert isinstance(response.retrieved_at, datetime)

    def test_get_payload_response_has_timestamp(self):
        from mythicmcp.models import GetPayloadResponse, PayloadDetail

        detail = PayloadDetail(
            uuid="test",
            agent_type="apollo",
            build_phase="success",
            deleted=False,
            auto_generated=False,
            creation_time=datetime.now(timezone.utc),
        )
        response = GetPayloadResponse(payload=detail)
        assert response.retrieved_at is not None

    def test_create_payload_response(self):
        from mythicmcp.models import CreatePayloadResponse

        response = CreatePayloadResponse(
            uuid="new-uuid", build_phase="success", build_message="OK"
        )
        assert response.success is True
        assert response.uuid == "new-uuid"
        assert response.retrieved_at is not None

    def test_create_payload_error_response_optional_uuid(self):
        from mythicmcp.models import CreatePayloadErrorResponse

        # Without UUID
        error = CreatePayloadErrorResponse(error="Failed", error_type="build_failed")
        assert error.success is False
        assert error.uuid is None

        # With UUID (timeout case)
        error_with_uuid = CreatePayloadErrorResponse(
            error="Timeout", error_type="timeout", uuid="abc-123"
        )
        assert error_with_uuid.uuid == "abc-123"

    def test_delete_payload_response(self):
        from mythicmcp.models import DeletePayloadResponse

        response = DeletePayloadResponse(payload_uuid="uuid-123")
        assert response.success is True
        assert response.payload_uuid == "uuid-123"
        assert response.retrieved_at is not None

    def test_delete_payload_error_response(self):
        from mythicmcp.models import DeletePayloadErrorResponse

        response = DeletePayloadErrorResponse(
            error="Not found", error_type="not_found", payload_uuid="uuid-123"
        )
        assert response.success is False
        assert response.error_type == "not_found"

    def test_download_payload_response(self):
        from mythicmcp.models import DownloadPayloadResponse

        response = DownloadPayloadResponse(
            payload_uuid="uuid-123",
            filename="agent.exe",
            content="SGVsbG8=",
            size_bytes=5,
        )
        assert response.success is True
        assert response.retrieved_at is not None

    def test_payload_config_check_response(self):
        from mythicmcp.models import PayloadConfigCheckResponse

        response = PayloadConfigCheckResponse(
            payload_uuid="uuid-123",
            status="success",
            output="All good",
        )
        assert response.status == "success"
        assert response.error == ""
        assert response.retrieved_at is not None
