"""Mythic connection lifecycle management.

Provides async context manager for Mythic connection that integrates with FastMCP lifespan.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator
from urllib.parse import urlparse

from mythic import mythic

from mythicmcp.config import ConfigurationError, MythicConfig, load_config

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from mythic import mythic_classes

logger = logging.getLogger(__name__)


class MythicConnectionError(Exception):
    """Raised when connection to Mythic server fails."""

    pass


class MythicAuthenticationError(Exception):
    """Raised when authentication with Mythic server fails."""

    pass


@dataclass
class MythicContext:
    """Context object holding Mythic connection state.

    Attributes:
        mythic: Authenticated Mythic instance
        config: Configuration used for connection
    """

    mythic: mythic_classes.Mythic
    config: MythicConfig


def _parse_server_url(server_url: str) -> tuple[str, int, bool]:
    """Parse server URL into host, port, and ssl components.

    Args:
        server_url: Full URL like https://localhost:7443

    Returns:
        Tuple of (host, port, use_ssl)
    """
    parsed = urlparse(server_url)
    host = parsed.hostname or "localhost"
    use_ssl = parsed.scheme == "https"
    default_port = 7443 if use_ssl else 7444
    port = parsed.port or default_port
    return host, port, use_ssl


async def connect_to_mythic(config: MythicConfig) -> mythic_classes.Mythic:
    """Establish connection to Mythic server.

    Args:
        config: Validated MythicConfig object

    Returns:
        Authenticated Mythic instance

    Raises:
        MythicConnectionError: If server is unreachable
        MythicAuthenticationError: If authentication fails
    """
    host, port, use_ssl = _parse_server_url(config.server_url)

    try:
        if config.uses_api_token:
            mythic_instance = await mythic.login(
                server_ip=host,
                server_port=port,
                ssl=use_ssl,
                apitoken=config.api_token,
                timeout=config.timeout,
            )
        else:
            mythic_instance = await mythic.login(
                server_ip=host,
                server_port=port,
                ssl=use_ssl,
                username=config.username,
                password=config.password,
                timeout=config.timeout,
            )

        # Verify we have a valid connection by checking current operation
        if not mythic_instance.current_operation_id:
            logger.warning(
                "No current operation set in Mythic. Some operations may fail. "
                "Set a current operation in the Mythic UI."
            )

        return mythic_instance

    except Exception as e:
        error_msg = str(e).lower()
        # Sanitize error message to never include credentials
        if "authentication" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
            raise MythicAuthenticationError(
                f"Mythic authentication failed. Verify your credentials are correct."
            ) from e
        elif "connection" in error_msg or "refused" in error_msg or "timeout" in error_msg:
            raise MythicConnectionError(
                f"Cannot reach Mythic server at {config.safe_server_url}. "
                f"Verify the server is running and accessible."
            ) from e
        else:
            raise MythicConnectionError(
                f"Failed to connect to Mythic server: {type(e).__name__}"
            ) from e


@asynccontextmanager
async def mythic_lifespan(server: FastMCP) -> AsyncIterator[MythicContext]:
    """FastMCP lifespan context manager for Mythic connection.

    Initializes Mythic connection at server startup and cleans up on shutdown.
    Fails fast if credentials are invalid (Constitution Principle V).

    Args:
        server: FastMCP server instance

    Yields:
        MythicContext: Context with authenticated Mythic instance

    Raises:
        ConfigurationError: If configuration is invalid
        MythicConnectionError: If server is unreachable
        MythicAuthenticationError: If authentication fails
    """
    logger.info("Initializing Mythic connection...")

    try:
        config = load_config()
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise

    try:
        mythic_instance = await connect_to_mythic(config)
        logger.info(f"Connected to Mythic server at {config.safe_server_url}")

        yield MythicContext(mythic=mythic_instance, config=config)

    except (MythicConnectionError, MythicAuthenticationError) as e:
        logger.error(f"Mythic connection failed: {e}")
        raise

    finally:
        logger.info("Mythic connection closed")
