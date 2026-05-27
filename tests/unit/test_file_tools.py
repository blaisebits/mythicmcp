"""Integration tests for file management MCP tools.

These tests verify that file management tools are properly registered
and configured through the MythicMCP server.
"""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Expected file tools that MythicMCP should expose
FILE_TOOLS = {
    "core_upload_file",
    "core_download_file",
    "core_list_downloaded_files",
    "core_list_uploaded_files",
}


class TestFileToolRegistration:
    """Test file tool registration without starting the server."""

    def test_all_file_tools_registered(self):
        """Verify all file tools are registered with the MCP server."""
        from mythicmcp.server import mcp

        registered_tools = set(mcp._tool_manager._tools.keys())

        missing_tools = FILE_TOOLS - registered_tools
        assert not missing_tools, f"Missing file tools: {missing_tools}"

    def test_file_tools_have_descriptions(self):
        """Verify all file tools have descriptions for discoverability."""
        from mythicmcp.server import mcp

        for tool_name in FILE_TOOLS:
            tool = mcp._tool_manager._tools.get(tool_name)
            assert tool is not None, f"Tool '{tool_name}' not found"
            assert tool.description, f"Tool '{tool_name}' has no description"
            assert len(tool.description) > 10, f"Tool '{tool_name}' has too short description"


class TestCoreUploadFileTool:
    """Test core_upload_file tool configuration."""

    def test_tool_exists(self):
        """Verify core_upload_file tool is registered."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_upload_file")
        assert tool is not None

    def test_tool_has_proper_description(self):
        """Verify tool description mentions upload and file."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_upload_file")
        desc_lower = tool.description.lower()
        assert "upload" in desc_lower
        assert "file" in desc_lower

    def test_tool_has_required_parameters(self):
        """Verify tool has filename, content, and file_path parameters."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_upload_file")
        # Parameters is a JSON schema dict with 'properties' and 'required' keys
        param_names = set(tool.parameters.get("properties", {}).keys())
        assert "filename" in param_names
        assert "content" in param_names
        assert "file_path" in param_names

    def test_tool_description_mentions_base64_rules_and_file_path(self):
        """Verify upload doc spells out the safer usage."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_upload_file")
        desc_lower = tool.description.lower()
        assert "base64" in desc_lower
        assert "file_path" in desc_lower
        assert "not both" in desc_lower


class TestCoreDownloadFileTool:
    """Test core_download_file tool configuration."""

    def test_tool_exists(self):
        """Verify core_download_file tool is registered."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_download_file")
        assert tool is not None

    def test_tool_has_proper_description(self):
        """Verify tool description mentions download and file."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_download_file")
        desc_lower = tool.description.lower()
        assert "download" in desc_lower
        assert "file" in desc_lower

    def test_tool_has_uuid_parameter(self):
        """Verify tool has file_uuid parameter."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_download_file")
        # Parameters is a JSON schema dict with 'properties' and 'required' keys
        param_names = set(tool.parameters.get("properties", {}).keys())
        assert "file_uuid" in param_names


class TestCoreListDownloadedFilesTool:
    """Test core_list_downloaded_files tool configuration."""

    def test_tool_exists(self):
        """Verify core_list_downloaded_files tool is registered."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_downloaded_files")
        assert tool is not None

    def test_tool_has_proper_description(self):
        """Verify tool description mentions list and downloaded."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_downloaded_files")
        desc_lower = tool.description.lower()
        assert "list" in desc_lower or "files" in desc_lower
        assert "download" in desc_lower

    def test_tool_has_no_required_parameters(self):
        """Verify tool doesn't require parameters (uses current operation)."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_downloaded_files")
        # Parameters is a JSON schema dict with 'required' key (list of required param names)
        required_params = tool.parameters.get("required", [])
        assert len(required_params) == 0, "List downloaded files should not require parameters"


class TestCoreListUploadedFilesTool:
    """Test core_list_uploaded_files tool configuration."""

    def test_tool_exists(self):
        """Verify core_list_uploaded_files tool is registered."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_uploaded_files")
        assert tool is not None

    def test_tool_has_proper_description(self):
        """Verify tool description mentions list and uploaded."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_uploaded_files")
        desc_lower = tool.description.lower()
        assert "list" in desc_lower or "files" in desc_lower
        assert "upload" in desc_lower

    def test_tool_has_no_required_parameters(self):
        """Verify tool doesn't require parameters (uses current operation)."""
        from mythicmcp.server import mcp

        tool = mcp._tool_manager._tools.get("core_list_uploaded_files")
        # Parameters is a JSON schema dict with 'required' key (list of required param names)
        required_params = tool.parameters.get("required", [])
        assert len(required_params) == 0, "List uploaded files should not require parameters"


class TestFileModels:
    """Test file-related Pydantic models."""

    def test_upload_file_response_model(self):
        """Verify UploadFileResponse model exists and has required fields."""
        from mythicmcp.models import UploadFileResponse

        # Create a valid response
        response = UploadFileResponse(
            file_id="test-uuid-1234",
            filename="test.txt",
            message="Test message",
        )
        assert response.success is True
        assert response.file_id == "test-uuid-1234"
        assert response.filename == "test.txt"
        assert response.retrieved_at is not None

    def test_upload_file_error_response_model(self):
        """Verify UploadFileErrorResponse model exists and has required fields."""
        from mythicmcp.models import UploadFileErrorResponse

        response = UploadFileErrorResponse(
            error="Test error",
            error_type="test_error",
        )
        assert response.success is False
        assert response.error == "Test error"
        assert response.error_type == "test_error"

    def test_download_file_response_model(self):
        """Verify DownloadFileResponse model exists and has required fields."""
        from mythicmcp.models import DownloadFileResponse

        response = DownloadFileResponse(
            file_uuid="test-uuid-1234",
            filename="test.txt",
            content=base64.b64encode(b"test content").decode(),
            size_bytes=12,
        )
        assert response.success is True
        assert response.file_uuid == "test-uuid-1234"
        assert response.size_bytes == 12

    def test_download_file_error_response_model(self):
        """Verify DownloadFileErrorResponse model exists and has required fields."""
        from mythicmcp.models import DownloadFileErrorResponse

        response = DownloadFileErrorResponse(
            error="File not found",
            error_type="not_found",
            file_uuid="test-uuid",
        )
        assert response.success is False
        assert response.error_type == "not_found"

    def test_list_downloaded_files_response_model(self):
        """Verify ListDownloadedFilesResponse model exists and has required fields."""
        from mythicmcp.models import ListDownloadedFilesResponse

        response = ListDownloadedFilesResponse(
            files=[],
            count=0,
        )
        assert response.files == []
        assert response.count == 0
        assert response.retrieved_at is not None

    def test_list_uploaded_files_response_model(self):
        """Verify ListUploadedFilesResponse model exists and has required fields."""
        from mythicmcp.models import ListUploadedFilesResponse

        response = ListUploadedFilesResponse(
            files=[],
            count=0,
        )
        assert response.files == []
        assert response.count == 0
        assert response.retrieved_at is not None


class TestFileHelperFunctions:
    """Test file tool helper functions."""

    def test_base64_decode_valid(self):
        """Test base64 decoding of valid content."""
        from mythicmcp.tools.files import _decode_base64_content

        encoded = base64.b64encode(b"hello world").decode()
        decoded = _decode_base64_content(encoded)
        assert decoded == b"hello world"

    def test_base64_decode_allows_whitespace(self):
        """Whitespace/newlines in base64 are ignored."""
        from mythicmcp.tools.files import _decode_base64_content

        decoded = _decode_base64_content("aGVs\nbG8g\nd29y bGQ=")
        assert decoded == b"hello world"

    def test_base64_decode_invalid(self):
        """Test base64 decoding raises error for invalid content."""
        from mythicmcp.tools.files import InvalidBase64Error, _decode_base64_content

        with pytest.raises(InvalidBase64Error, match="chunk markers"):
            _decode_base64_content("not-valid-base64!!!")

    @pytest.mark.asyncio
    async def test_core_upload_file_accepts_local_file_path(self, tmp_path):
        """Local file path upload reads bytes and derives filename."""
        from mythicmcp.tools.files import core_upload_file

        sample = tmp_path / "sample.bin"
        sample.write_bytes(b"coff-bytes")

        mock_ctx = MagicMock()
        mock_ctx.request_context.lifespan_context.mythic = MagicMock()

        with patch("mythicmcp.tools.files.upload_file", new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value.file_id = "uuid-1234"
            mock_upload.return_value.filename = "sample.bin"
            mock_upload.return_value.message = "ok"
            mock_upload.return_value.success = True

            await core_upload_file(mock_ctx, file_path=str(sample))

            mock_upload.assert_awaited_once()
            assert mock_upload.await_args.args[1] == "sample.bin"
            assert mock_upload.await_args.args[2] == b"coff-bytes"

    @pytest.mark.asyncio
    async def test_core_upload_file_rejects_conflicting_inputs(self):
        """content and file_path together should fail fast."""
        from mythicmcp.tools.files import core_upload_file

        mock_ctx = MagicMock()
        mock_ctx.request_context.lifespan_context.mythic = MagicMock()

        result = await core_upload_file(
            mock_ctx,
            filename="x.bin",
            content=base64.b64encode(b"abc").decode(),
            file_path="C:\\temp\\x.bin",
        )

        assert result.success is False
        assert result.error_type == "invalid_input"
        assert "either 'content' or 'file_path'" in result.error

    def test_file_exceptions_exist(self):
        """Verify all file exception classes exist."""
        from mythicmcp.tools.files import (
            ConnectionError,
            FileError,
            FileNotFoundError,
            FileUploadError,
            InvalidBase64Error,
            NoOperationError,
        )

        # Test exception messages
        e1 = FileNotFoundError("test-uuid")
        assert "test-uuid" in str(e1)

        e2 = FileUploadError("test.txt", "reason")
        assert "test.txt" in str(e2)
        assert "reason" in str(e2)

        e3 = InvalidBase64Error("details")
        assert "details" in str(e3)

        e4 = NoOperationError()
        assert "operation" in str(e4).lower()

        e5 = ConnectionError("details")
        assert "details" in str(e5)
