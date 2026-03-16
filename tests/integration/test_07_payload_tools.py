"""Integration tests for core payload tools.

Tests the payload tool business logic functions against a live Mythic server.
Uses the first configured agent from the integration config to create a test
payload, then exercises list, get, download, config check, and redirect rules.

These tests are self-contained and do not depend on the numbered pipeline
(test_02 through test_06). They only require a running Mythic server with
at least one payload type container available.
"""

from __future__ import annotations

import json

import pytest

from tests.integration.config_models import IntegrationTestConfig


pytestmark = pytest.mark.integration


# Module-level state to share payload UUID across tests
_created_payload_uuid: str | None = None


class TestListPayloads:
    """Test core_list_payloads business logic."""

    async def test_list_payloads_returns_response(self, mythic_instance):
        """List payloads should return a valid response with count."""
        from mythicmcp.tools.payloads import list_payloads

        result = await list_payloads(mythic_instance)

        assert result is not None
        assert hasattr(result, "payloads")
        assert hasattr(result, "count")
        assert result.count == len(result.payloads)
        assert result.retrieved_at is not None

    async def test_list_payloads_summaries_have_required_fields(self, mythic_instance):
        """Each payload summary should contain expected fields."""
        from mythicmcp.tools.payloads import list_payloads

        result = await list_payloads(mythic_instance)

        # May be empty if fresh server — that's fine
        for payload in result.payloads:
            assert payload.uuid, "Payload UUID should not be empty"
            assert payload.build_phase in ("building", "success", "error"), (
                f"Unexpected build_phase: {payload.build_phase}"
            )
            assert isinstance(payload.deleted, bool)
            assert isinstance(payload.auto_generated, bool)
            assert payload.creation_time is not None


class TestCreatePayload:
    """Test core_create_payload business logic."""

    async def test_create_payload_success(
        self, mythic_instance, integration_config: IntegrationTestConfig
    ):
        """Create a payload using the first agent config and verify build succeeds."""
        global _created_payload_uuid

        from mythicmcp.tools.payloads import create_payload

        agent = integration_config.agents[0]

        c2_profiles = [
            {
                "c2_profile": p.c2_profile,
                "c2_profile_parameters": p.c2_profile_parameters,
            }
            for p in agent.c2_profiles
        ]

        build_parameters = [
            {"name": p.name, "value": p.value}
            for p in agent.build_parameters
        ]

        result = await create_payload(
            mythic_instance,
            payload_type_name=agent.payload_type,
            filename=f"mcp_payload_test_{agent.name}",
            operating_system=agent.os,
            c2_profiles=c2_profiles,
            build_parameters=build_parameters or None,
            description="MythicMCP payload tools integration test",
            timeout=integration_config.timeouts.payload_generation,
        )

        assert result.success is True, f"Build failed: {result.build_message}"
        assert result.uuid, "Payload UUID should not be empty"
        assert result.build_phase == "success"

        # Store for subsequent tests
        _created_payload_uuid = result.uuid

    async def test_create_payload_invalid_type_fails(self, mythic_instance):
        """Create with nonexistent agent type should raise an error."""
        from mythicmcp.tools.payloads import PayloadBuildError, create_payload

        with pytest.raises((PayloadBuildError, Exception)):
            await create_payload(
                mythic_instance,
                payload_type_name="nonexistent_agent_type_xyz",
                filename="should_fail.exe",
                operating_system="Windows",
                c2_profiles=[{
                    "c2_profile": "http",
                    "c2_profile_parameters": {"callback_host": "https://fake"},
                }],
                timeout=60,
            )


class TestGetPayload:
    """Test core_get_payload business logic."""

    async def test_get_payload_returns_detail(self, mythic_instance):
        """Get payload detail for the created payload."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import get_payload_by_uuid

        result = await get_payload_by_uuid(mythic_instance, _created_payload_uuid)

        assert result.payload.uuid == _created_payload_uuid
        assert result.payload.build_phase == "success"
        assert result.payload.agent_type, "Agent type should not be empty"
        assert result.payload.creation_time is not None
        assert result.retrieved_at is not None

    async def test_get_payload_has_file_metadata(self, mythic_instance):
        """Successfully built payload should have file metadata."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import get_payload_by_uuid

        result = await get_payload_by_uuid(mythic_instance, _created_payload_uuid)

        assert result.payload.file_uuid is not None, "Built payload should have file_uuid"
        assert result.payload.filename is not None, "Built payload should have filename"

    async def test_get_payload_has_c2_profiles(self, mythic_instance):
        """Payload detail should include C2 profile information."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import get_payload_by_uuid

        result = await get_payload_by_uuid(mythic_instance, _created_payload_uuid)

        assert len(result.payload.c2_profiles) > 0, "Should have at least one C2 profile"
        for profile in result.payload.c2_profiles:
            assert profile.name, "C2 profile name should not be empty"

    async def test_get_payload_invalid_uuid(self, mythic_instance):
        """Get payload with nonexistent UUID should raise not-found error."""
        from mythicmcp.tools.payloads import PayloadNotFoundError, get_payload_by_uuid

        with pytest.raises(PayloadNotFoundError):
            await get_payload_by_uuid(mythic_instance, "00000000-0000-0000-0000-000000000000")


class TestDownloadPayload:
    """Test core_download_payload business logic."""

    async def test_download_payload_returns_content(self, mythic_instance):
        """Download the built payload and verify non-empty base64 content."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import download_payload

        result = await download_payload(mythic_instance, _created_payload_uuid)

        assert result.success is True
        assert result.payload_uuid == _created_payload_uuid
        assert result.filename, "Filename should not be empty"
        assert result.content, "Content should not be empty"
        assert result.size_bytes > 0, "Size should be positive"
        assert result.retrieved_at is not None

    async def test_download_payload_invalid_uuid(self, mythic_instance):
        """Download with nonexistent UUID should raise not-found error."""
        from mythicmcp.tools.payloads import PayloadNotFoundError, download_payload

        with pytest.raises(PayloadNotFoundError):
            await download_payload(mythic_instance, "00000000-0000-0000-0000-000000000000")


class TestCheckPayloadConfig:
    """Test core_check_payload_config business logic."""

    async def test_check_config_returns_result(self, mythic_instance):
        """Config check should return a status and output."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import check_payload_config

        result = await check_payload_config(mythic_instance, _created_payload_uuid)

        assert result.payload_uuid == _created_payload_uuid
        assert result.status in ("success", "error"), f"Unexpected status: {result.status}"
        assert result.retrieved_at is not None


class TestPayloadRedirectRules:
    """Test core_payload_redirect_rules business logic."""

    async def test_redirect_rules_returns_result(self, mythic_instance):
        """Redirect rules should return a status and output."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import payload_redirect_rules

        result = await payload_redirect_rules(mythic_instance, _created_payload_uuid)

        assert result.payload_uuid == _created_payload_uuid
        assert result.status in ("success", "error"), f"Unexpected status: {result.status}"
        assert result.retrieved_at is not None


class TestDeletePayload:
    """Test core_delete_payload business logic."""

    async def test_delete_payload_success(self, mythic_instance):
        """Delete the created payload and verify success."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import delete_payload

        result = await delete_payload(mythic_instance, _created_payload_uuid)

        assert result.success is True
        assert result.payload_uuid == _created_payload_uuid
        assert result.retrieved_at is not None

    async def test_deleted_payload_shows_deleted_flag(self, mythic_instance):
        """After deletion, get_payload should show deleted=True."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import get_payload_by_uuid

        result = await get_payload_by_uuid(mythic_instance, _created_payload_uuid)
        assert result.payload.deleted is True

    async def test_delete_payload_invalid_uuid(self, mythic_instance):
        """Delete with nonexistent UUID should raise an error."""
        from mythicmcp.tools.payloads import delete_payload

        with pytest.raises(Exception):
            await delete_payload(mythic_instance, "00000000-0000-0000-0000-000000000000")


class TestListPayloadsAfterCreate:
    """Verify list includes the created payload."""

    async def test_created_payload_appears_in_list(self, mythic_instance):
        """The payload we created should appear in the list results."""
        if not _created_payload_uuid:
            pytest.skip("No payload created in previous test")

        from mythicmcp.tools.payloads import list_payloads

        result = await list_payloads(mythic_instance)

        uuids = [p.uuid for p in result.payloads]
        assert _created_payload_uuid in uuids, (
            f"Created payload {_created_payload_uuid} not found in list of {result.count} payloads"
        )


class TestCoreEntryPointsJSONParsing:
    """Test JSON parsing helpers used by core_create_payload entry point."""

    def test_parse_c2_profiles_valid(self):
        """Valid C2 profiles JSON should parse correctly."""
        from mythicmcp.tools.payloads import _parse_c2_profiles_json

        result = _parse_c2_profiles_json(
            '[{"c2_profile": "http", "c2_profile_parameters": {"callback_host": "https://test"}}]'
        )
        assert len(result) == 1
        assert result[0]["c2_profile"] == "http"

    def test_parse_c2_profiles_invalid_json(self):
        """Malformed JSON should raise InvalidJSONError."""
        from mythicmcp.tools.payloads import InvalidJSONError, _parse_c2_profiles_json

        with pytest.raises(InvalidJSONError):
            _parse_c2_profiles_json("not valid json")

    def test_parse_c2_profiles_missing_key(self):
        """Missing required key should raise InvalidJSONError."""
        from mythicmcp.tools.payloads import InvalidJSONError, _parse_c2_profiles_json

        with pytest.raises(InvalidJSONError):
            _parse_c2_profiles_json('[{"wrong_key": "http"}]')

    def test_parse_c2_profiles_empty_raises(self):
        """Empty string should raise InvalidJSONError (C2 profiles are required)."""
        from mythicmcp.tools.payloads import InvalidJSONError, _parse_c2_profiles_json

        with pytest.raises(InvalidJSONError):
            _parse_c2_profiles_json("")

    def test_parse_build_parameters_valid(self):
        """Valid build parameters JSON should parse correctly."""
        from mythicmcp.tools.payloads import _parse_build_parameters_json

        result = _parse_build_parameters_json('[{"name": "key", "value": "val"}]')
        assert len(result) == 1

    def test_parse_build_parameters_empty_returns_list(self):
        """Empty string should return empty list (build params are optional)."""
        from mythicmcp.tools.payloads import _parse_build_parameters_json

        assert _parse_build_parameters_json("") == []

    def test_parse_commands_valid(self):
        """Valid commands JSON should parse correctly."""
        from mythicmcp.tools.payloads import _parse_commands_json

        result = _parse_commands_json('["shell", "ls", "cat"]')
        assert result == ["shell", "ls", "cat"]

    def test_parse_commands_empty_returns_list(self):
        """Empty string should return empty list (commands are optional)."""
        from mythicmcp.tools.payloads import _parse_commands_json

        assert _parse_commands_json("") == []
