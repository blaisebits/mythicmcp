"""Unit tests for mythicmcp.config module."""

import os
from unittest.mock import patch

import pytest

from mythicmcp.config import ConfigurationError, MythicConfig, load_config


class TestMythicConfig:
    """Tests for MythicConfig dataclass."""

    def test_valid_config_with_api_token(self):
        """Config is valid with server URL and API token."""
        config = MythicConfig(
            server_url="https://mythic.local:7443",
            api_token="test-token-123",
        )
        assert config.server_url == "https://mythic.local:7443"
        assert config.api_token == "test-token-123"
        assert config.uses_api_token is True

    def test_valid_config_with_credentials(self):
        """Config is valid with server URL and username/password."""
        config = MythicConfig(
            server_url="https://mythic.local:7443",
            username="admin",
            password="password123",
        )
        assert config.username == "admin"
        assert config.password == "password123"
        assert config.uses_api_token is False

    def test_missing_server_url_raises_error(self):
        """ConfigurationError raised when server URL is empty."""
        with pytest.raises(ConfigurationError, match="MYTHIC_SERVER_URL is required"):
            MythicConfig(server_url="", api_token="token")

    def test_missing_auth_raises_error(self):
        """ConfigurationError raised when no auth provided."""
        with pytest.raises(ConfigurationError, match="Either MYTHIC_API_TOKEN or"):
            MythicConfig(server_url="https://mythic.local:7443")

    def test_partial_credentials_raises_error(self):
        """ConfigurationError raised when only username provided."""
        with pytest.raises(ConfigurationError, match="Either MYTHIC_API_TOKEN or"):
            MythicConfig(
                server_url="https://mythic.local:7443",
                username="admin",
            )

    def test_both_auth_methods_raises_error(self):
        """ConfigurationError raised when both token and credentials provided."""
        with pytest.raises(ConfigurationError, match="not both"):
            MythicConfig(
                server_url="https://mythic.local:7443",
                api_token="token",
                username="admin",
                password="password",
            )

    def test_default_timeout(self):
        """Default timeout is 30 seconds."""
        config = MythicConfig(
            server_url="https://mythic.local:7443",
            api_token="token",
        )
        assert config.timeout == 30

    def test_custom_timeout(self):
        """Custom timeout is accepted."""
        config = MythicConfig(
            server_url="https://mythic.local:7443",
            api_token="token",
            timeout=60,
        )
        assert config.timeout == 60

    def test_safe_server_url_strips_credentials(self):
        """safe_server_url removes embedded credentials."""
        config = MythicConfig(
            server_url="https://user:pass@mythic.local:7443",
            api_token="token",
        )
        # Should not contain user:pass
        assert "user" not in config.safe_server_url
        assert "pass" not in config.safe_server_url
        assert "mythic.local" in config.safe_server_url


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_env_with_token(self):
        """load_config reads from environment variables (API token)."""
        env = {
            "MYTHIC_SERVER_URL": "https://mythic.example.com:7443",
            "MYTHIC_API_TOKEN": "env-token-456",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.server_url == "https://mythic.example.com:7443"
            assert config.api_token == "env-token-456"

    def test_load_config_from_env_with_credentials(self):
        """load_config reads from environment variables (credentials)."""
        env = {
            "MYTHIC_SERVER_URL": "https://mythic.example.com:7443",
            "MYTHIC_USERNAME": "testuser",
            "MYTHIC_PASSWORD": "testpass",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.username == "testuser"
            assert config.password == "testpass"

    def test_load_config_custom_timeout(self):
        """load_config parses MYTHIC_TIMEOUT."""
        env = {
            "MYTHIC_SERVER_URL": "https://mythic.example.com:7443",
            "MYTHIC_API_TOKEN": "token",
            "MYTHIC_TIMEOUT": "120",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.timeout == 120

    def test_load_config_invalid_timeout_raises_error(self):
        """load_config raises error for non-integer timeout."""
        env = {
            "MYTHIC_SERVER_URL": "https://mythic.example.com:7443",
            "MYTHIC_API_TOKEN": "token",
            "MYTHIC_TIMEOUT": "not-a-number",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigurationError, match="must be an integer"):
                load_config()

    def test_load_config_missing_url_raises_error(self):
        """load_config raises error when MYTHIC_SERVER_URL missing."""
        env = {"MYTHIC_API_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigurationError, match="MYTHIC_SERVER_URL is required"):
                load_config()
