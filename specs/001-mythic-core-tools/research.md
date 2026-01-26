# Research: Mythic Framework Core Tools

**Feature**: 001-mythic-core-tools
**Date**: 2026-01-25

## Technology Decisions

### MCP Server Framework

**Decision**: Use FastMCP (part of `mcp` package v1.26.0+)

**Rationale**:
- Official Anthropic/MCP Python SDK
- Decorator-based tool registration (`@mcp.tool()`)
- Built-in async support - both sync and async tool functions supported
- Automatic JSON Schema generation from type annotations
- Pydantic model support for structured parameters and return types
- Lifespan context manager for connection lifecycle management

**Alternatives Considered**:
- Low-level `mcp.server.Server` class: More control but requires manual JSON-RPC handling
- Third-party MCP implementations: Less maintained, not official

**Key Pattern**:
```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("MythicMCP")

@mcp.tool()
async def core_list_callbacks() -> list[dict]:
    """List all active Mythic callbacks."""
    # Implementation
```

### Mythic Python Library

**Decision**: Use `mythic` package v0.2.10+ (async-only API)

**Rationale**:
- Official Mythic scripting library
- 70+ async functions covering all Mythic operations
- GraphQL backend via `gql` library (pinned to 3.5.3)
- Supports both username/password and API token authentication
- Well-documented callback and operation queries

**Key Functions for This Feature**:
| Function | Purpose |
|----------|---------|
| `mythic.login()` | Authenticate and get Mythic instance |
| `mythic.get_all_active_callbacks()` | List active callbacks (US1) |
| `mythic.get_operations()` | Get operation metadata (US2) |
| GraphQL custom query | Get single callback by ID (US4) |

**Important Notes**:
- All functions are `async` and must be awaited
- SSL is hardcoded to `False` in HTTP transports (v0.2.9+)
- No current operation set causes many API calls to fail

### Connection Lifecycle

**Decision**: Use FastMCP lifespan context manager for Mythic connection

**Rationale**:
- Initialize Mythic connection once at server startup
- Share connection across all tool invocations
- Clean disconnect on server shutdown
- Fail-safe: prevent startup if credentials invalid

**Pattern**:
```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

@dataclass
class MythicContext:
    mythic: mythic_classes.Mythic

@asynccontextmanager
async def mythic_lifespan(server: FastMCP) -> AsyncIterator[MythicContext]:
    mythic_instance = await mythic.login(...)
    try:
        yield MythicContext(mythic=mythic_instance)
    finally:
        # Cleanup if needed
        pass
```

### Error Handling

**Decision**: Use structured error responses with descriptive messages

**Rationale**:
- Constitution requires "no silent failures" (Principle V)
- FR-005 requires "clear, descriptive errors"
- SC-002 requires "actionable troubleshooting information"

**Pattern**:
```python
from mcp.server.fastmcp import ToolError

@mcp.tool()
async def core_list_callbacks(ctx: Context) -> list[dict]:
    """List active callbacks from Mythic."""
    try:
        mythic_ctx = ctx.request_context.lifespan_context
        callbacks = await mythic.get_all_active_callbacks(mythic_ctx.mythic)
        return callbacks
    except AuthenticationError as e:
        raise ToolError(f"Mythic authentication failed: {e.message}")
    except ConnectionError as e:
        raise ToolError(f"Cannot reach Mythic server: {e.message}")
```

### Configuration Management

**Decision**: Environment variables with validation at startup

**Rationale**:
- Constitution requires credential validation at startup (Principle V)
- FR-006 requires credentials never in responses/logs
- Standard practice for MCP servers

**Environment Variables**:
| Variable | Required | Description |
|----------|----------|-------------|
| `MYTHIC_SERVER_URL` | Yes | Mythic server URL (e.g., `https://mythic.local:7443`) |
| `MYTHIC_API_TOKEN` | No* | Pre-generated API token |
| `MYTHIC_USERNAME` | No* | Username for login |
| `MYTHIC_PASSWORD` | No* | Password for login |

*Either API token OR username/password required

## Callback Data Model

From `graphql_queries.callback_fragment`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Internal callback ID |
| `display_id` | int | Human-readable callback number |
| `host` | string | Hostname |
| `user` | string | Username |
| `domain` | string | Domain name |
| `ip` | string | Internal IP |
| `external_ip` | string | External IP |
| `os` | string | Operating system |
| `architecture` | string | CPU architecture |
| `pid` | int | Process ID |
| `process_name` | string | Process name |
| `integrity_level` | int | Windows integrity level |
| `description` | string | Callback description |
| `agent_callback_id` | string | Agent-specific ID |
| `operation_id` | int | Parent operation ID |
| `payload.payloadtype.name` | string | Agent type name |
| `sleep_info` | string | Sleep/jitter info |
| `extra_info` | string | Additional metadata |

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| How to get single callback by ID? | Use custom GraphQL query with `where: {id: {_eq: $id}}` |
| How to check server connectivity? | Attempt login and check for exceptions |
| How to get operation details? | Use `mythic.get_operations()` function |
| How to handle session expiration? | Catch auth exceptions, raise ToolError with re-auth suggestion |
