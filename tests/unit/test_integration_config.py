"""Unit tests for integration test YAML config loading and validation."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from tests.lab_config import MYTHIC_CALLBACK_HOST, MYTHIC_SERVER_URL
from tests.integration.config_models import (
    IntegrationTestConfig,
    load_integration_config,
)


def _valid_config() -> dict:
    """Return a minimal valid config dict."""
    return {
        "mythic": {
            "server_url": MYTHIC_SERVER_URL,
            "api_token": "test-token",
        },
        "agents": [
            {
                "name": "apollo",
                "payload_type": "apollo",
                "os": "Windows",
                "filename": "test.exe",
                "c2_profiles": [
                    {
                        "c2_profile": "http",
                        "c2_profile_parameters": {"callback_host": MYTHIC_CALLBACK_HOST},
                    }
                ],
            }
        ],
        "targets": [
            {
                "name": "win-target",
                "hostname": "WIN-PC",
                "os": "Windows",
                "callback_id": 1,
                "upload_path": "C:\\test.exe",
                "agents": ["apollo"],
            }
        ],
        "test_commands": {
            "apollo": [
                {"command": "shell", "parameters": {"command": "whoami"}},
            ]
        },
    }


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    """Write a config dict to a YAML file and return the path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(data))
    return config_file


class TestValidConfigLoading:
    """Test that valid configs load correctly."""

    def test_valid_config_loads_all_fields(self, tmp_path: Path):
        data = _valid_config()
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert config.mythic.server_url == MYTHIC_SERVER_URL
        assert config.mythic.api_token == "test-token"
        assert len(config.agents) == 1
        assert config.agents[0].name == "apollo"
        assert len(config.targets) == 1
        assert config.targets[0].hostname == "WIN-PC"
        assert len(config.test_commands["apollo"]) == 1

    def test_default_timeouts_applied(self, tmp_path: Path):
        data = _valid_config()
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert config.timeouts.payload_generation == 300
        assert config.timeouts.callback_verification == 120
        assert config.timeouts.command_execution == 60
        assert config.timeouts.polling_interval == 5

    def test_custom_timeouts_override_defaults(self, tmp_path: Path):
        data = _valid_config()
        data["timeouts"] = {"payload_generation": 600, "polling_interval": 10}
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert config.timeouts.payload_generation == 600
        assert config.timeouts.polling_interval == 10
        # Unset fields keep defaults
        assert config.timeouts.callback_verification == 120

    def test_username_password_auth(self, tmp_path: Path):
        data = _valid_config()
        data["mythic"] = {
            "server_url": MYTHIC_SERVER_URL,
            "username": "admin",
            "password": "pass123",
        }
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert config.mythic.username == "admin"
        assert config.mythic.password == "pass123"
        assert config.mythic.api_token is None

    def test_build_parameters_loaded(self, tmp_path: Path):
        data = _valid_config()
        data["agents"][0]["build_parameters"] = [
            {"name": "param1", "value": "val1"},
        ]
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert len(config.agents[0].build_parameters) == 1
        assert config.agents[0].build_parameters[0].name == "param1"

    def test_multiple_agents_and_targets(self, tmp_path: Path):
        data = _valid_config()
        data["agents"].append(
            {
                "name": "arachne",
                "payload_type": "arachne",
                "os": "Linux",
                "filename": "test_arachne",
                "c2_profiles": [
                    {
                        "c2_profile": "http",
                        "c2_profile_parameters": {"callback_host": MYTHIC_CALLBACK_HOST},
                    }
                ],
            }
        )
        data["targets"].append(
            {
                "name": "linux-target",
                "hostname": "debian-vm",
                "os": "Linux",
                "callback_id": 2,
                "upload_path": "/tmp/payload",
                "agents": ["arachne"],
            }
        )
        data["test_commands"]["arachne"] = [
            {"command": "shell", "parameters": {"command": "id"}},
        ]
        config_file = _write_yaml(tmp_path, data)
        config = load_integration_config(str(config_file))

        assert len(config.agents) == 2
        assert len(config.targets) == 2


class TestMissingRequiredFields:
    """Test that missing required fields produce ValidationError."""

    def test_missing_server_url(self, tmp_path: Path):
        data = _valid_config()
        del data["mythic"]["server_url"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "server_url" in str(exc_info.value)

    def test_missing_auth_credentials(self, tmp_path: Path):
        data = _valid_config()
        data["mythic"] = {"server_url": MYTHIC_SERVER_URL}
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "api_token" in str(exc_info.value) or "username" in str(exc_info.value)

    def test_missing_agent_name(self, tmp_path: Path):
        data = _valid_config()
        del data["agents"][0]["name"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "name" in str(exc_info.value)

    def test_missing_target_hostname(self, tmp_path: Path):
        data = _valid_config()
        del data["targets"][0]["hostname"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "hostname" in str(exc_info.value)

    def test_missing_agents_list(self, tmp_path: Path):
        data = _valid_config()
        del data["agents"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "agents" in str(exc_info.value)

    def test_missing_targets_list(self, tmp_path: Path):
        data = _valid_config()
        del data["targets"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "targets" in str(exc_info.value)


class TestCrossValidation:
    """Test cross-validation between agents, targets, and test_commands."""

    def test_invalid_agent_reference_in_target(self, tmp_path: Path):
        data = _valid_config()
        data["targets"][0]["agents"] = ["nonexistent"]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "nonexistent" in str(exc_info.value)

    def test_os_incompatibility(self, tmp_path: Path):
        data = _valid_config()
        # Apollo is Windows but target is Linux
        data["targets"][0]["os"] = "Linux"
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "incompatible" in str(exc_info.value)

    def test_invalid_test_commands_key(self, tmp_path: Path):
        data = _valid_config()
        data["test_commands"]["nonexistent_agent"] = [
            {"command": "shell", "parameters": {}}
        ]
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "nonexistent_agent" in str(exc_info.value)

    def test_duplicate_agent_names(self, tmp_path: Path):
        data = _valid_config()
        # Add a second agent with the same name
        data["agents"].append(data["agents"][0].copy())
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        assert "Duplicate" in str(exc_info.value)

    def test_empty_agents_list(self, tmp_path: Path):
        data = _valid_config()
        data["agents"] = []
        data["targets"] = []
        data["test_commands"] = {}
        config_file = _write_yaml(tmp_path, data)

        with pytest.raises(ValidationError) as exc_info:
            load_integration_config(str(config_file))
        # Either empty agents or empty targets should fail
        error_str = str(exc_info.value)
        assert "empty" in error_str.lower() or "agents" in error_str.lower()


class TestConfigFileResolution:
    """Test config file path resolution."""

    def test_missing_config_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_integration_config("/nonexistent/path/config.yaml")

    def test_env_var_overrides_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        data = _valid_config()
        config_file = _write_yaml(tmp_path, data)
        monkeypatch.setenv("MYTHICMCP_TEST_CONFIG", str(config_file))

        config = load_integration_config()
        assert config.mythic.server_url == MYTHIC_SERVER_URL

    def test_explicit_path_used(self, tmp_path: Path):
        data = _valid_config()
        config_file = _write_yaml(tmp_path, data)

        config = load_integration_config(str(config_file))
        assert config.mythic.server_url == MYTHIC_SERVER_URL

    def test_env_var_takes_precedence_over_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Env var config
        env_data = _valid_config()
        env_data["mythic"]["server_url"] = "https://env-server:7443"
        env_file = tmp_path / "env_config.yaml"
        env_file.write_text(yaml.dump(env_data))
        monkeypatch.setenv("MYTHICMCP_TEST_CONFIG", str(env_file))

        # Path argument config (should be ignored)
        path_data = _valid_config()
        path_data["mythic"]["server_url"] = "https://path-server:7443"
        path_file = tmp_path / "path_config.yaml"
        path_file.write_text(yaml.dump(path_data))

        config = load_integration_config(str(path_file))
        assert config.mythic.server_url == "https://env-server:7443"
