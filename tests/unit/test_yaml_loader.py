"""Tests for YAML-based agent plugin configuration loader.

Covers:
- T016: Missing required fields
- T017: Invalid field values
- T018: YAML parse errors
- T019: Unrecognized top-level keys
- T020: Validation error field paths
- T020a: Duplicate agent name across files
- T021: Minimal agent config
- T022: Multi-command agent with mixed types
- T023: External plugin directory discovery
- T024: Coexistence with code-based plugins
"""

from __future__ import annotations

import logging
import os
import textwrap
from pathlib import Path
from typing import Any

import pytest

from mythicmcp.plugins.yaml_loader import (
    AgentConfigModel,
    CommandConfigModel,
    ParameterConfigModel,
    YamlConfigError,
    YamlConfigModel,
    build_handler,
    build_parameter_model,
    discover_yaml_configs,
    load_yaml_plugin,
    parse_yaml_config,
)


def _write_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    """Helper to write a YAML file and return its path."""
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content))
    return path


def _minimal_config() -> dict[str, Any]:
    """Return a minimal valid config dict."""
    return {
        "agent": {
            "name": "testagent",
            "description": "Test agent",
            "supported_os": ["Windows"],
        },
        "commands": [
            {
                "name": "ping",
                "description": "Ping command",
            }
        ],
    }


# =============================================================================
# T016: Missing required fields
# =============================================================================


class TestMissingRequiredFields:
    """Test that missing required fields produce validation errors."""

    def test_missing_agent_name(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              description: "Test"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("name" in e["field"] for e in result.errors)

    def test_missing_agent_description(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("description" in e["field"] for e in result.errors)

    def test_missing_agent_supported_os(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("supported_os" in e["field"] for e in result.errors)

    def test_missing_commands(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("commands" in e["field"] for e in result.errors)

    def test_command_missing_name(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - description: "Ping command"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_command_missing_description(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_parameter_missing_name(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - type: string
                    description: "A parameter"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_parameter_missing_type(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: target
                    description: "Target host"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_parameter_missing_description(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: target
                    type: string
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)


# =============================================================================
# T017: Invalid field values
# =============================================================================


class TestInvalidFieldValues:
    """Test that invalid field values produce validation errors."""

    def test_unsupported_parameter_type(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: count
                    type: float
                    description: "Count"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("float" in e["message"] for e in result.errors)

    def test_invalid_agent_name_uppercase(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: TestAgent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_invalid_agent_name_special_chars(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: test_agent!
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_invalid_agent_name_too_long(self, tmp_path: Path) -> None:
        long_name = "a" * 51
        path = _write_yaml(tmp_path, "test.yaml", f"""
            agent:
              name: {long_name}
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_invalid_supported_os(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - FreeBSD
            commands:
              - name: ping
                description: "Ping command"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("FreeBSD" in e["message"] for e in result.errors)

    def test_timeout_too_low(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                timeout: 10
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_timeout_too_high(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                timeout: 500
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_duplicate_command_names(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "First ping"
              - name: ping
                description: "Second ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("Duplicate" in e["message"] or "duplicate" in e["message"].lower() for e in result.errors)

    def test_reserved_param_name_callback_id(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: callback_id
                    type: integer
                    description: "Callback"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("reserved" in e["message"].lower() for e in result.errors)

    def test_reserved_param_name_timeout(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: timeout
                    type: integer
                    description: "Timeout"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("reserved" in e["message"].lower() for e in result.errors)

    def test_reserved_param_name_ctx(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: ctx
                    type: string
                    description: "Context"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("reserved" in e["message"].lower() for e in result.errors)

    def test_reserved_param_name_context(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: context
                    type: string
                    description: "Context"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_reserved_param_name_self(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: self
                    type: string
                    description: "Self"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_min_greater_than_max(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: count
                    type: integer
                    description: "Count"
                    min: 10
                    max: 5
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_default_type_mismatch(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: count
                    type: integer
                    description: "Count"
                    default: "not a number"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)

    def test_choices_on_integer_param(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: count
                    type: integer
                    description: "Count"
                    choices:
                      - "1"
                      - "2"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("choices" in e["message"].lower() for e in result.errors)

    def test_min_max_on_string_param(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: target
                    type: string
                    description: "Target"
                    min: 1
                    max: 100
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("min" in e["message"].lower() for e in result.errors)

    def test_empty_commands_list(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands: []
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)


# =============================================================================
# T018: YAML parse errors
# =============================================================================


class TestYamlParseErrors:
    """Test that YAML parse errors are handled gracefully."""

    def test_malformed_yaml(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent
              supported_os:
                - Windows
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert result.agent_name == "unknown"
        assert any("YAML" in e["message"] or "yaml" in e["message"] for e in result.errors)

    def test_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("")
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("empty" in e["message"].lower() for e in result.errors)

    def test_file_with_only_comments(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            # This is just a comment
            # No actual content
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("empty" in e["message"].lower() or "comment" in e["message"].lower() for e in result.errors)

    def test_non_dict_top_level(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            - item1
            - item2
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert any("mapping" in e["message"].lower() for e in result.errors)


# =============================================================================
# T019: Unrecognized top-level keys
# =============================================================================


class TestUnrecognizedKeys:
    """Test that unrecognized top-level keys produce warnings but still load."""

    def test_unrecognized_keys_warning(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
            some_unknown_key:
              version: "1.0"
        """)
        with caplog.at_level(logging.WARNING):
            result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        assert result.agent.name == "testagent"
        assert "some_unknown_key" in caplog.text


# =============================================================================
# T020: Validation error field paths
# =============================================================================


class TestValidationErrorFieldPaths:
    """Test that validation errors include file path and specific field paths."""

    def test_error_includes_file_path(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              description: "Test"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert str(path) in result.file_path

    def test_error_includes_agent_name_when_parseable(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert result.agent_name == "testagent"

    def test_error_shows_unknown_agent_when_unparseable(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("")
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        assert result.agent_name == "unknown"

    def test_error_str_includes_details(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test"
              supported_os:
                - FreeBSD
            commands:
              - name: ping
                description: "Ping"
        """)
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigError)
        error_str = str(result)
        assert "testagent" in error_str or str(path) in error_str


# =============================================================================
# T020a: Duplicate agent name across files
# =============================================================================


class TestDuplicateAgentNameAcrossFiles:
    """Test that two YAML configs defining the same agent name both fail to load."""

    def test_duplicate_agent_name_second_rejected(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "agent1.yaml", """
            agent:
              name: myagent
              description: "First agent"
              supported_os:
                - Windows
            commands:
              - name: cmd1
                description: "Command 1"
        """)
        _write_yaml(tmp_path, "agent2.yaml", """
            agent:
              name: myagent
              description: "Second agent"
              supported_os:
                - Linux
            commands:
              - name: cmd2
                description: "Command 2"
        """)
        from mythicmcp.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        yaml_paths = discover_yaml_configs(tmp_path)
        assert len(yaml_paths) == 2

        loaded = []
        for yaml_path in yaml_paths:
            result = load_yaml_plugin(yaml_path)
            if not isinstance(result, YamlConfigError):
                success = registry.register_plugin(result)
                loaded.append((yaml_path.name, success))

        # First should succeed, second should fail (duplicate)
        assert loaded[0][1] is True
        assert loaded[1][1] is False


# =============================================================================
# T021: Minimal agent config
# =============================================================================


class TestMinimalAgentConfig:
    """Test that a minimal agent config produces a valid plugin."""

    def test_minimal_config_produces_valid_plugin(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "minimal.yaml", """
            agent:
              name: minimal
              description: "Minimal test agent"
              supported_os:
                - Linux
            commands:
              - name: ping
                description: "Ping command"
                parameters:
                  - name: target
                    type: string
                    description: "Target host"
                    required: true
        """)
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)

        assert result.agent_name == "minimal"
        assert result.agent_description == "Minimal test agent"
        assert result.supported_os == ["Linux"]

        tools = result.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "ping"
        assert tools[0].description == "Ping command"

        # Verify parameter model
        fields = tools[0].parameters.model_fields
        assert "callback_id" in fields
        assert "target" in fields
        assert "timeout" in fields
        assert fields["callback_id"].annotation is int
        assert fields["target"].annotation is str
        assert fields["timeout"].default == 60


# =============================================================================
# T022: Multi-command agent with mixed types
# =============================================================================


class TestMultiCommandAgent:
    """Test a multi-command agent with mixed parameter types."""

    def test_three_commands_mixed_types(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "multi.yaml", """
            agent:
              name: multi
              description: "Multi-command agent"
              supported_os:
                - Windows
                - Linux
            commands:
              - name: search
                description: "Search for files"
                timeout: 90
                parameters:
                  - name: query
                    type: string
                    description: "Search query"
                    required: true
                  - name: max_results
                    type: integer
                    description: "Max results to return"
                    default: 10
                    min: 1
                    max: 100

              - name: delete
                description: "Delete a file"
                timeout: 60
                parameters:
                  - name: path
                    type: string
                    description: "File path"
                    required: true
                  - name: force
                    type: boolean
                    description: "Force delete"
                    default: false

              - name: status
                description: "Get agent status"
                timeout: 30
        """)
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)

        tools = result.get_tools()
        assert len(tools) == 3

        # Verify search command
        search = next(t for t in tools if t.name == "search")
        search_fields = search.parameters.model_fields
        assert list(search_fields.keys()) == ["callback_id", "query", "max_results", "timeout"]
        assert search_fields["max_results"].default == 10
        assert search_fields["timeout"].default == 90

        # Verify delete command
        delete = next(t for t in tools if t.name == "delete")
        delete_fields = delete.parameters.model_fields
        assert list(delete_fields.keys()) == ["callback_id", "path", "force", "timeout"]
        assert delete_fields["force"].annotation is bool
        assert delete_fields["force"].default is False

        # Verify status command (no params)
        status = next(t for t in tools if t.name == "status")
        status_fields = status.parameters.model_fields
        assert list(status_fields.keys()) == ["callback_id", "timeout"]
        assert status_fields["timeout"].default == 30


# =============================================================================
# T023: External plugin directory discovery
# =============================================================================


class TestExternalPluginDirectory:
    """Test YAML discovery from external plugins directory."""

    def test_discover_yaml_from_external_dir(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "custom.yaml", """
            agent:
              name: custom
              description: "Custom external agent"
              supported_os:
                - Linux
            commands:
              - name: exec
                description: "Execute command"
        """)

        configs = discover_yaml_configs(tmp_path)
        assert len(configs) == 1
        assert configs[0].name == "custom.yaml"

    def test_discover_skips_dotfiles(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, ".hidden.yaml", """
            agent:
              name: hidden
              description: "Hidden agent"
              supported_os: [Windows]
            commands:
              - name: cmd
                description: "Command"
        """)
        configs = discover_yaml_configs(tmp_path)
        assert len(configs) == 0

    def test_discover_skips_underscore_files(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "_template.yaml", """
            agent:
              name: template
              description: "Template agent"
              supported_os: [Windows]
            commands:
              - name: cmd
                description: "Command"
        """)
        configs = discover_yaml_configs(tmp_path)
        assert len(configs) == 0

    def test_discover_yml_extension(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "agent.yml", """
            agent:
              name: ymlagent
              description: "YML agent"
              supported_os: [Linux]
            commands:
              - name: cmd
                description: "Command"
        """)
        configs = discover_yaml_configs(tmp_path)
        assert len(configs) == 1

    def test_discover_nonexistent_directory(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "nonexistent"
        configs = discover_yaml_configs(nonexistent)
        assert configs == []

    def test_external_dir_via_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_yaml(tmp_path, "external.yaml", """
            agent:
              name: external
              description: "External agent"
              supported_os:
                - macOS
            commands:
              - name: hello
                description: "Hello command"
        """)
        monkeypatch.setenv("MYTHICMCP_PLUGINS_DIR", str(tmp_path))

        from mythicmcp.plugins import _registry, load_all_plugins

        _registry.clear()
        registry = load_all_plugins()

        assert "external" in registry.list_plugins()
        _registry.clear()


# =============================================================================
# T024: Coexistence with code-based plugins
# =============================================================================


class TestBuiltinPlugins:
    """Test that all builtin YAML plugins load correctly."""

    def test_builtin_yaml_plugins_load(self) -> None:
        from mythicmcp.plugins import _registry, load_all_plugins

        _registry.clear()
        registry = load_all_plugins()

        plugins = registry.list_plugins()
        assert "apollo" in plugins  # from YAML
        assert "arachne" in plugins  # from YAML
        assert "poseidon" in plugins  # from YAML

        # Verify tool counts
        all_tools = registry.get_all_tools()
        apollo_tools = [n for n in all_tools if n.startswith("apollo_")]
        arachne_tools = [n for n in all_tools if n.startswith("arachne_")]
        poseidon_tools = [n for n in all_tools if n.startswith("poseidon_")]
        assert len(apollo_tools) == 78
        assert len(arachne_tools) == 8
        assert len(poseidon_tools) == 74

        _registry.clear()


# =============================================================================
# Additional model-level tests
# =============================================================================


class TestParameterModelBuilder:
    """Test dynamic Pydantic model building."""

    def test_required_param_model(self) -> None:
        cmd = CommandConfigModel(
            name="test",
            description="Test command",
            parameters=[
                ParameterConfigModel(
                    name="target",
                    type="string",
                    description="Target host",
                    required=True,
                )
            ],
        )
        model = build_parameter_model(cmd, "agent")
        fields = model.model_fields

        assert fields["callback_id"].is_required()
        assert fields["target"].is_required()
        assert not fields["timeout"].is_required()
        assert fields["timeout"].default == 60

    def test_optional_param_with_default(self) -> None:
        cmd = CommandConfigModel(
            name="test",
            description="Test command",
            timeout=90,
            parameters=[
                ParameterConfigModel(
                    name="count",
                    type="integer",
                    description="Count",
                    default=5,
                    min=1,
                    max=100,
                )
            ],
        )
        model = build_parameter_model(cmd, "agent")
        fields = model.model_fields

        assert fields["count"].default == 5
        assert not fields["count"].is_required()
        assert fields["timeout"].default == 90

    def test_boolean_param(self) -> None:
        cmd = CommandConfigModel(
            name="test",
            description="Test command",
            parameters=[
                ParameterConfigModel(
                    name="verbose",
                    type="boolean",
                    description="Verbose output",
                    default=False,
                )
            ],
        )
        model = build_parameter_model(cmd, "agent")
        assert model.model_fields["verbose"].annotation is bool
        assert model.model_fields["verbose"].default is False

    def test_beacon_args_param_accepts_string_and_typed_pairs(self) -> None:
        cmd = CommandConfigModel(
            name="execute_coff",
            description="Execute COFF",
            parameters=[
                ParameterConfigModel(
                    name="coff_arguments",
                    type="beacon_args",
                    description="Typed Beacon arguments",
                    default="",
                )
            ],
        )
        model = build_parameter_model(cmd, "apollo")

        string_value = model(callback_id=5, coff_arguments="wchar:\"DC01\"")
        typed_value = model(
            callback_id=5,
            coff_arguments=[
                ["wchar", "DC01"],
                ["int32", 123],
                ["bool", True],
            ],
        )

        assert string_value.coff_arguments == 'wchar:"DC01"'
        assert typed_value.coff_arguments == [
            ("wchar", "DC01"),
            ("int32", 123),
            ("bool", True),
        ]


class TestHandlerBuilder:
    """Test handler function generation."""

    def test_handler_is_async_callable(self) -> None:
        agent = AgentConfigModel(
            name="test",
            description="Test",
            supported_os=["Windows"],
        )
        cmd = CommandConfigModel(
            name="shell",
            description="Shell command",
            parameters=[
                ParameterConfigModel(
                    name="command",
                    type="string",
                    description="Command to run",
                    required=True,
                )
            ],
        )
        handler = build_handler(agent, cmd)
        import asyncio

        assert asyncio.iscoroutinefunction(handler)


class TestApolloYamlConfig:
    """Verify the builtin Apollo YAML config loads correctly."""

    def test_apollo_yaml_loads(self) -> None:
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "apollo.yaml"
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)
        assert result.agent_name == "apollo"
        assert len(result.get_tools()) == 78

    def test_apollo_tool_names(self) -> None:
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "apollo.yaml"
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)
        tool_names = sorted(t.name for t in result.get_tools())
        assert tool_names == sorted([
            "assembly_inject", "blockdlls", "cat", "cd", "cp", "dcsync",
            "download", "execute_assembly", "execute_coff", "execute_pe",
            "exit", "get_injection_techniques", "getprivs", "getsystem",
            "ifconfig", "inject", "inline_assembly", "jobkill", "jobs",
            "jump_psexec", "jump_wmi", "keylog_inject", "kill", "ldap_query",
            "link", "listpipes", "load", "ls", "make_token", "mimikatz",
            "mkdir", "mv", "net_dclist", "net_localgroup",
            "net_localgroup_member", "net_shares", "netstat", "powerpick",
            "powershell", "powershell_import", "ppid", "printspoofer", "ps",
            "psinject", "pth", "pwd", "reg_query", "reg_write_value",
            "register_assembly", "register_coff", "register_file", "rev2self",
            "rm", "rpfwd", "run", "sc", "screenshot", "screenshot_inject",
            "set_injection_technique", "shell", "shinject", "sleep", "socks",
            "spawn", "spawnto_x64", "spawnto_x86", "steal_token",
            "ticket_cache_add", "ticket_cache_extract", "ticket_cache_list",
            "ticket_cache_purge", "ticket_store_add", "ticket_store_list",
            "ticket_store_purge", "unlink", "upload", "whoami", "wmiexecute",
        ])

    def test_apollo_execute_coff_uses_beacon_args_schema(self) -> None:
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "apollo.yaml"
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)

        execute_coff = next(t for t in result.get_tools() if t.name == "execute_coff")
        field = execute_coff.parameters.model_fields["coff_arguments"]
        schema = execute_coff.parameters.model_json_schema()
        coff_schema = schema["properties"]["coff_arguments"]

        assert field.default == ""
        assert "anyOf" in coff_schema

        typed_args = execute_coff.parameters(
            callback_id=5,
            coff_name="sa-wmi_query.x64.o",
            coff_arguments=[
                ["wchar", "DC01"],
                ["wchar", "root\\cimv2"],
            ],
        )

        assert typed_args.coff_arguments == [
            ("wchar", "DC01"),
            ("wchar", "root\\cimv2"),
        ]


# =============================================================================
# Metadata field tests (T004, T005)
# =============================================================================


class TestMetadataField:
    """Test metadata field parsing on YamlConfigModel."""

    def test_metadata_field_parsed_without_warnings(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """T004: YAML with metadata section loads without warnings."""
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
            metadata:
              agent_version: "1.0.0"
              mythic_version: "3.4.6+"
        """)
        with caplog.at_level(logging.WARNING):
            result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        assert result.metadata == {"agent_version": "1.0.0", "mythic_version": "3.4.6+"}
        assert "metadata" not in caplog.text
        assert "Unrecognized" not in caplog.text

    def test_metadata_field_absent_loads(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """T005: YAML without metadata still loads (backward compat)."""
        path = _write_yaml(tmp_path, "test.yaml", """
            agent:
              name: testagent
              description: "Test agent"
              supported_os:
                - Windows
            commands:
              - name: ping
                description: "Ping command"
        """)
        with caplog.at_level(logging.WARNING):
            result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        assert result.metadata is None
        assert "Unrecognized" not in caplog.text

    def test_apollo_yaml_metadata_accessible(self) -> None:
        """T028: Verify metadata dict is accessible on loaded apollo.yaml."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "apollo.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        assert result.metadata is not None
        assert "agent_version" in result.metadata
        assert result.metadata["agent_version"] == "2.4.8"

    def test_arachne_yaml_metadata_accessible(self) -> None:
        """T029: Verify metadata dict is accessible on loaded arachne.yaml."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "arachne.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        assert result.metadata is not None
        assert "agent_version" in result.metadata


# =============================================================================
# Poseidon YAML Config Tests
# =============================================================================


class TestPoseidonYamlConfig:
    """Verify the builtin Poseidon YAML config loads correctly."""

    @staticmethod
    def _poseidon_path() -> Path:
        return Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"

    def test_poseidon_yaml_loads(self) -> None:
        """Poseidon YAML loads without validation errors."""
        result = load_yaml_plugin(self._poseidon_path())
        assert not isinstance(result, YamlConfigError), f"Load failed: {result}"

    def test_poseidon_command_count(self) -> None:
        """Poseidon has >= 70 commands (74 expected)."""
        result = load_yaml_plugin(self._poseidon_path())
        assert not isinstance(result, YamlConfigError)
        tools = result.get_tools()
        assert len(tools) >= 70, f"Expected >= 70 tools, got {len(tools)}"
        assert len(tools) == 74

    def test_poseidon_agent_metadata(self) -> None:
        """Poseidon agent name, description, supported_os are correct."""
        result = load_yaml_plugin(self._poseidon_path())
        assert not isinstance(result, YamlConfigError)
        assert result.agent_name == "poseidon"
        assert "macOS" in result.agent_description or "Poseidon" in result.agent_description
        assert set(result.supported_os) == {"macOS", "Linux"}

    def test_poseidon_metadata_version(self) -> None:
        """Poseidon metadata includes agent_version 2.2.8."""
        result = parse_yaml_config(self._poseidon_path())
        assert isinstance(result, YamlConfigModel)
        assert result.metadata is not None
        assert result.metadata["agent_version"] == "2.2.8"


class TestPoseidonSpotChecks:
    """Spot-check specific Poseidon commands for correct parameter definitions."""

    @staticmethod
    def _load_poseidon_tools() -> list:
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"
        result = load_yaml_plugin(path)
        assert not isinstance(result, YamlConfigError)
        return result.get_tools()

    def _find_tool(self, name: str):
        tools = self._load_poseidon_tools()
        matches = [t for t in tools if t.name == name]
        assert len(matches) == 1, f"Tool '{name}' not found"
        return matches[0]

    def test_shell_has_command_param(self) -> None:
        """shell command has required string 'command' parameter."""
        tool = self._find_tool("shell")
        fields = tool.parameters.model_fields
        assert "command" in fields
        assert fields["command"].annotation is str
        assert fields["command"].is_required()

    def test_curl_has_method_choices(self) -> None:
        """curl command has 'method' param with choices field."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        curl_cmd = next(c for c in result.commands if c.name == "curl")
        method_param = next(p for p in curl_cmd.parameters if p.name == "method")
        assert method_param.choices is not None
        assert "GET" in method_param.choices
        assert "POST" in method_param.choices

    def test_portscan_has_hosts_param(self) -> None:
        """portscan command has required 'hosts' parameter."""
        tool = self._find_tool("portscan")
        fields = tool.parameters.model_fields
        assert "hosts" in fields
        assert fields["hosts"].is_required()

    def test_upload_has_file_id_and_remote_path(self) -> None:
        """upload command has 'file_id' (required) and 'remote_path' params."""
        tool = self._find_tool("upload")
        fields = tool.parameters.model_fields
        assert "file_id" in fields
        assert "remote_path" in fields
        assert fields["file_id"].is_required()

    def test_jxa_macos_has_mythic_command(self) -> None:
        """jxa_macos command has mythic_command set to 'jxa'."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        jxa_cmd = next(c for c in result.commands if c.name == "jxa_macos")
        assert jxa_cmd.mythic_command == "jxa"

    def test_macos_commands_have_mythic_command_mapping(self) -> None:
        """All _macos suffixed commands have mythic_command without the suffix."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        macos_cmds = [c for c in result.commands if c.name.endswith("_macos")]
        assert len(macos_cmds) >= 20, f"Expected >= 20 macOS commands, got {len(macos_cmds)}"
        for cmd in macos_cmds:
            assert cmd.mythic_command is not None, f"{cmd.name} missing mythic_command"
            assert not cmd.mythic_command.endswith("_macos"), (
                f"{cmd.name} mythic_command should not end with _macos, got '{cmd.mythic_command}'"
            )

    def test_macos_descriptions_have_prefix(self) -> None:
        """All _macos commands have '(macOS only)' in description."""
        path = Path(__file__).parent.parent.parent / "src" / "mythicmcp" / "plugins" / "builtin" / "poseidon.yaml"
        result = parse_yaml_config(path)
        assert isinstance(result, YamlConfigModel)
        macos_cmds = [c for c in result.commands if c.name.endswith("_macos")]
        for cmd in macos_cmds:
            assert "(macOS only)" in cmd.description, (
                f"{cmd.name} description missing '(macOS only)': {cmd.description}"
            )
