"""Pydantic models for integration test YAML configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class MythicConnectionConfig(BaseModel):
    """Mythic server connection configuration."""

    server_url: str
    api_token: str | None = None
    username: str | None = None
    password: str | None = None
    timeout: int = 30

    @model_validator(mode="after")
    def validate_auth(self) -> MythicConnectionConfig:
        has_token = self.api_token is not None
        has_creds = self.username is not None and self.password is not None
        if not has_token and not has_creds:
            raise ValueError(
                "Either 'api_token' or both 'username' and 'password' must be provided"
            )
        return self


class TimeoutConfig(BaseModel):
    """Timeout defaults for test phases."""

    payload_generation: int = 300
    callback_verification: int = 120
    command_execution: int = 60
    polling_interval: int = 5


class C2ProfileConfig(BaseModel):
    """C2 profile configuration for payload generation."""

    c2_profile: str
    c2_profile_parameters: dict[str, Any]


class BuildParam(BaseModel):
    """Build parameter for payload generation."""

    name: str
    value: str


class AgentConfig(BaseModel):
    """Agent type definition for payload generation."""

    name: str
    payload_type: str
    os: str
    filename: str
    c2_profiles: list[C2ProfileConfig]
    build_parameters: list[BuildParam] = Field(default_factory=list)
    description: str = ""


class TargetConfig(BaseModel):
    """Target system definition."""

    name: str
    hostname: str
    os: str
    callback_id: int
    upload_path: str
    agents: list[str]


class TestCommandConfig(BaseModel):
    """Test command configuration for a specific agent type."""

    command: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_output: str | None = None
    timeout: int = 60


class IntegrationTestConfig(BaseModel):
    """Top-level integration test configuration."""

    mythic: MythicConnectionConfig
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    agents: list[AgentConfig]
    targets: list[TargetConfig]
    test_commands: dict[str, list[TestCommandConfig]]

    @model_validator(mode="after")
    def cross_validate(self) -> IntegrationTestConfig:
        agent_names = {a.name for a in self.agents}
        agent_os_map = {a.name: a.os for a in self.agents}

        # Check for duplicate agent names
        if len(agent_names) != len(self.agents):
            seen: set[str] = set()
            dupes: list[str] = []
            for a in self.agents:
                if a.name in seen:
                    dupes.append(a.name)
                seen.add(a.name)
            raise ValueError(f"Duplicate agent names: {dupes}")

        # Validate agents list is not empty
        if not self.agents:
            raise ValueError("'agents' list must not be empty")

        # Validate targets list is not empty
        if not self.targets:
            raise ValueError("'targets' list must not be empty")

        # Validate target agent references exist
        for target in self.targets:
            for agent_ref in target.agents:
                if agent_ref not in agent_names:
                    raise ValueError(
                        f"Target '{target.name}' references unknown agent '{agent_ref}'. "
                        f"Available agents: {sorted(agent_names)}"
                    )

            # Validate OS compatibility between agent and target
            for agent_ref in target.agents:
                agent_os = agent_os_map[agent_ref]
                if agent_os != target.os:
                    raise ValueError(
                        f"Agent '{agent_ref}' (os={agent_os}) is incompatible with "
                        f"target '{target.name}' (os={target.os})"
                    )

        # Validate test_commands keys match agent names
        for cmd_agent in self.test_commands:
            if cmd_agent not in agent_names:
                raise ValueError(
                    f"test_commands key '{cmd_agent}' does not match any agent name. "
                    f"Available agents: {sorted(agent_names)}"
                )

        return self


# Default config path relative to repository root
_DEFAULT_CONFIG_PATH = Path("tests/integration/config.yaml")


def load_integration_config(path: str | None = None) -> IntegrationTestConfig:
    """Load and validate the YAML integration test configuration.

    Resolution order:
    1. MYTHICMCP_TEST_CONFIG environment variable
    2. Explicit path argument
    3. Default: tests/integration/config.yaml (relative to repo root)

    Raises:
        FileNotFoundError: Config file does not exist.
        pydantic.ValidationError: Config has invalid structure or values.
    """
    # Determine config path
    env_path = os.environ.get("MYTHICMCP_TEST_CONFIG")
    if env_path:
        config_path = Path(env_path)
    elif path:
        config_path = Path(path)
    else:
        # Find repo root by looking for pyproject.toml
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                config_path = current / _DEFAULT_CONFIG_PATH
                break
            current = current.parent
        else:
            config_path = _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Integration test config not found: {config_path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    return IntegrationTestConfig.model_validate(raw)
