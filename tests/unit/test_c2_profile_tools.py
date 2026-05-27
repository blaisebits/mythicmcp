"""Tests for C2 profile management tools."""

from __future__ import annotations

import pytest

from mythicmcp.models import (
    C2InstanceSummary,
    C2ParameterDefinition,
    C2ProfileErrorResponse,
    C2ProfileInfo,
    CreateC2InstanceResponse,
    DeleteC2InstanceResponse,
    GetC2InstanceResponse,
    GetC2ProfileParametersResponse,
    ListC2InstancesResponse,
    ListC2ProfilesResponse,
)


class TestC2ToolRegistration:
    """Tests that all C2 profile tools are registered with MCP."""

    C2_TOOLS = {
        "core_list_c2_profiles",
        "core_get_c2_profile_parameters",
        "core_create_c2_instance",
        "core_list_c2_instances",
        "core_get_c2_instance",
        "core_delete_c2_instance",
    }

    def test_all_c2_tools_registered(self):
        from mythicmcp.server import mcp

        registered = set(mcp._tool_manager._tools.keys())
        missing = self.C2_TOOLS - registered
        assert not missing, f"Missing C2 tools: {missing}"

    def test_c2_tools_have_descriptions(self):
        from mythicmcp.server import mcp

        for tool_name in self.C2_TOOLS:
            tool = mcp._tool_manager._tools.get(tool_name)
            assert tool is not None, f"Tool '{tool_name}' not found"
            assert tool.description, f"Tool '{tool_name}' has no description"
            assert len(tool.description) > 10


class TestC2ProfileModels:
    """Tests for C2 profile Pydantic response models."""

    def test_c2_profile_info(self):
        info = C2ProfileInfo(
            name="http",
            description="Uses HTTP Get/Post messages",
            is_p2p=False,
            running=True,
            container_running=True,
        )
        assert info.name == "http"
        assert not info.is_p2p
        assert info.running

    def test_list_c2_profiles_response(self):
        resp = ListC2ProfilesResponse(
            profiles=[
                C2ProfileInfo(
                    name="http", description="HTTP", is_p2p=False,
                    running=True, container_running=True,
                ),
                C2ProfileInfo(
                    name="tcp", description="TCP", is_p2p=True,
                    running=False, container_running=False,
                ),
            ],
            total_count=2,
        )
        assert resp.total_count == 2
        assert resp.profiles[1].is_p2p
        assert resp.retrieved_at is not None

    def test_c2_parameter_definition(self):
        param = C2ParameterDefinition(
            name="callback_host",
            description="Callback Host",
            default_value="https://domain.com",
            required=True,
            parameter_type="String",
        )
        assert param.required
        assert param.choices == []

    def test_c2_parameter_definition_with_choices(self):
        param = C2ParameterDefinition(
            name="AESPSK",
            description="Crypto type",
            default_value="aes256_hmac",
            required=False,
            parameter_type="ChooseOne",
            choices=["aes256_hmac", "none"],
        )
        assert len(param.choices) == 2
        assert "aes256_hmac" in param.choices

    def test_get_c2_profile_parameters_response(self):
        resp = GetC2ProfileParametersResponse(
            profile_name="http",
            parameters=[
                C2ParameterDefinition(
                    name="callback_host",
                    description="Callback Host",
                    default_value="https://domain.com",
                    required=True,
                    parameter_type="String",
                ),
            ],
            parameter_count=1,
        )
        assert resp.profile_name == "http"
        assert resp.parameter_count == 1

    def test_c2_instance_summary(self):
        summary = C2InstanceSummary(
            instance_name="http-staging",
            c2_profile_name="http",
        )
        assert summary.instance_name == "http-staging"

    def test_list_c2_instances_response(self):
        resp = ListC2InstancesResponse(
            instances=[
                C2InstanceSummary(instance_name="http-prod", c2_profile_name="http"),
            ],
            total_count=1,
        )
        assert resp.total_count == 1

    def test_get_c2_instance_response(self):
        resp = GetC2InstanceResponse(
            instance_name="http-staging",
            c2_profile_name="http",
            c2_parameters={"callback_host": "https://staging.example.com", "callback_port": 443},
        )
        assert resp.c2_parameters["callback_port"] == 443

    def test_create_c2_instance_response(self):
        resp = CreateC2InstanceResponse(
            instance_name="http-staging",
            c2_profile_name="http",
        )
        assert resp.success is True

    def test_delete_c2_instance_response(self):
        resp = DeleteC2InstanceResponse(
            instance_name="http-staging",
        )
        assert resp.success is True

    def test_c2_profile_error_response(self):
        resp = C2ProfileErrorResponse(
            error="Profile not found",
            error_type="not_found",
        )
        assert resp.success is False
        assert resp.error_type == "not_found"
        assert resp.retrieved_at is not None


class TestC2ProfileGraphQLQueries:
    """Tests that GraphQL query strings are well-formed."""

    def test_list_profiles_query_has_required_fields(self):
        from mythicmcp.tools.c2profiles import LIST_C2_PROFILES_QUERY

        assert "c2profile" in LIST_C2_PROFILES_QUERY
        assert "name" in LIST_C2_PROFILES_QUERY
        assert "is_p2p" in LIST_C2_PROFILES_QUERY
        assert "running" in LIST_C2_PROFILES_QUERY

    def test_get_parameters_query_has_filter(self):
        from mythicmcp.tools.c2profiles import GET_C2_PROFILE_PARAMETERS_QUERY

        assert "c2profileparameters" in GET_C2_PROFILE_PARAMETERS_QUERY
        assert "$c2_name" in GET_C2_PROFILE_PARAMETERS_QUERY
        assert "default_value" in GET_C2_PROFILE_PARAMETERS_QUERY
        assert "parameter_type" in GET_C2_PROFILE_PARAMETERS_QUERY

    def test_list_instances_query_has_required_fields(self):
        from mythicmcp.tools.c2profiles import LIST_C2_INSTANCES_QUERY

        assert "c2profileparametersinstance" in LIST_C2_INSTANCES_QUERY
        assert "instance_name" in LIST_C2_INSTANCES_QUERY

    def test_get_instance_query_has_filter(self):
        from mythicmcp.tools.c2profiles import GET_C2_INSTANCE_QUERY

        assert "$instance_name" in GET_C2_INSTANCE_QUERY
        assert "$c2_profile_id" in GET_C2_INSTANCE_QUERY
        assert "c2profileparameter" in GET_C2_INSTANCE_QUERY
        assert "value" in GET_C2_INSTANCE_QUERY

    def test_delete_instance_mutation_is_mutation(self):
        from mythicmcp.tools.c2profiles import DELETE_C2_INSTANCE_MUTATION

        assert "mutation" in DELETE_C2_INSTANCE_MUTATION
        assert "delete_c2profileparametersinstance" in DELETE_C2_INSTANCE_MUTATION
        assert "affected_rows" in DELETE_C2_INSTANCE_MUTATION


class TestC2InstanceValueCoercion:
    """Tests for saved C2 instance value coercion."""

    def test_number_values_are_coerced(self):
        from mythicmcp.tools.c2profiles import _coerce_c2_parameter_value

        assert _coerce_c2_parameter_value("Number", "80") == 80

    def test_boolean_values_are_coerced(self):
        from mythicmcp.tools.c2profiles import _coerce_c2_parameter_value

        assert _coerce_c2_parameter_value("Boolean", "true") is True
        assert _coerce_c2_parameter_value("Boolean", "false") is False

    def test_dictionary_values_are_coerced(self):
        from mythicmcp.tools.c2profiles import _coerce_c2_parameter_value

        result = _coerce_c2_parameter_value("Dictionary", '{"User-Agent":"Mozilla"}')
        assert result == {"User-Agent": "Mozilla"}

    def test_empty_dictionary_becomes_empty_object(self):
        from mythicmcp.tools.c2profiles import _coerce_c2_parameter_value

        assert _coerce_c2_parameter_value("Dictionary", "") == {}
