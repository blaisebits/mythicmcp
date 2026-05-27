"""Configuration management for MythicMCP.

Handles environment variable loading and validation for Mythic server credentials.
Credentials are validated at import time per Constitution Principle V (Fail-Safe Defaults).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""

    pass


def _parse_bool_env(var_name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    value = os.environ.get(var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_dev_mode_enabled() -> bool:
    """Check whether development-only tools should be exposed."""
    return _parse_bool_env("MYTHIC_DEV", default=False)


def is_hotload_enabled() -> bool:
    """Check whether dynamic agent load/unload tools should be exposed."""
    return _parse_bool_env("MYTHIC_HOTLOAD", default=True)


def get_startup_agents() -> list[str]:
    """Parse startup agent names from MYTHIC_AGENTS."""
    value = os.environ.get("MYTHIC_AGENTS", "")
    if not value.strip():
        return []

    seen: set[str] = set()
    agents: list[str] = []
    for raw_name in value.split(","):
        agent_name = raw_name.strip()
        if not agent_name or agent_name in seen:
            continue
        if agent_name.lower() == "all":
            return ["all"]
        seen.add(agent_name)
        agents.append(agent_name)

    return agents


@dataclass(frozen=True)
class MythicConfig:
    """Configuration for Mythic server connection.

    Attributes:
        server_url: Mythic server URL (e.g., https://mythic.local:7443)
        api_token: Pre-generated API token (mutually exclusive with username/password)
        username: Username for login (requires password)
        password: Password for login (requires username)
        timeout: Query timeout in seconds (default 30)
        plugins_dir: Directory for external plugins (optional)
    """

    server_url: str
    api_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    plugins_dir: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.server_url:
            raise ConfigurationError("MYTHIC_SERVER_URL is required")

        has_token = bool(self.api_token)
        has_credentials = bool(self.username and self.password)

        if not has_token and not has_credentials:
            raise ConfigurationError(
                "Either MYTHIC_API_TOKEN or both MYTHIC_USERNAME and MYTHIC_PASSWORD are required"
            )

        if has_token and has_credentials:
            raise ConfigurationError(
                "Provide either MYTHIC_API_TOKEN or MYTHIC_USERNAME/MYTHIC_PASSWORD, not both"
            )

    @property
    def uses_api_token(self) -> bool:
        """Check if configuration uses API token authentication."""
        return bool(self.api_token)

    @property
    def safe_server_url(self) -> str:
        """Return server URL without any embedded credentials."""
        # Parse and strip any potential auth info from URL
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(self.server_url)
        # Reconstruct without username/password
        safe_parsed = parsed._replace(netloc=f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname or "")
        return urlunparse(safe_parsed)


def load_config() -> MythicConfig:
    """Load configuration from environment variables.

    Environment Variables:
        MYTHIC_SERVER_URL: Required. Mythic server URL.
        MYTHIC_API_TOKEN: Optional. Pre-generated API token.
        MYTHIC_USERNAME: Optional. Username for login.
        MYTHIC_PASSWORD: Optional. Password for login.
        MYTHIC_TIMEOUT: Optional. Query timeout in seconds (default 30).

    Returns:
        MythicConfig: Validated configuration object.

    Raises:
        ConfigurationError: If configuration is invalid or incomplete.
    """
    timeout_str = os.environ.get("MYTHIC_TIMEOUT", "30")
    try:
        timeout = int(timeout_str)
    except ValueError:
        raise ConfigurationError(f"MYTHIC_TIMEOUT must be an integer, got: {timeout_str}")

    return MythicConfig(
        server_url=os.environ.get("MYTHIC_SERVER_URL", ""),
        api_token=os.environ.get("MYTHIC_API_TOKEN"),
        username=os.environ.get("MYTHIC_USERNAME"),
        password=os.environ.get("MYTHIC_PASSWORD"),
        timeout=timeout,
        plugins_dir=os.environ.get("MYTHICMCP_PLUGINS_DIR"),
    )
