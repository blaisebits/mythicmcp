# Implementation Plan: Mythic Framework Core Tools

**Branch**: `001-mythic-core-tools` | **Date**: 2026-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mythic-core-tools/spec.md`

## Summary

Implement the foundational MCP tools for interacting with Mythic C2 framework. This feature provides four core tools: listing active callbacks, retrieving callback details, viewing operation metadata, and checking server connectivity. All tools expose Mythic operations through the MCP protocol using the official `mcp` Python SDK and the `mythic` async library.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: mcp (1.26.0+), mythic (0.2.10+), pydantic
**Storage**: N/A (stateless - queries Mythic server)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux/macOS server (MCP stdio transport)
**Project Type**: Single project
**Performance Goals**: <5s response for callback list (up to 100 callbacks per SC-001)
**Constraints**: 30s default timeout for queries, no credential exposure
**Scale/Scope**: Single Mythic server connection, <1000 callbacks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I. MCP Protocol First | All tools exposed via MCP interfaces | ✅ Pass - Using FastMCP decorators |
| II. Async-Native | All I/O uses async/await | ✅ Pass - mythic library is async-only |
| III. Plugin Isolation | Core tools are agent-agnostic | ✅ Pass - No agent-specific logic |
| IV. Explicit Authorization | Tool descriptions state operations | ✅ Pass - Each tool describes Mythic action |
| V. Fail-Safe Defaults | Safe choices, no silent failures | ✅ Pass - Credential validation at startup |

**Security Requirements**:
- ✅ Mythic Authentication via API token or username/password
- ✅ Credentials never in responses/logs (FR-006)
- ✅ Connection validation before operations (FR-007)

## Project Structure

### Documentation (this feature)

```text
specs/001-mythic-core-tools/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (MCP tool schemas)
```

### Source Code (repository root)

```text
src/
├── mythicmcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server entry point
│   ├── config.py          # Configuration and credential handling
│   ├── connection.py      # Mythic connection management
│   └── tools/
│       ├── __init__.py
│       ├── callbacks.py   # core_list_callbacks, core_get_callback tools
│       ├── operations.py  # core_get_operation tool
│       └── status.py      # core_check_connection tool

tests/
├── conftest.py            # Shared fixtures (mock Mythic)
├── unit/
│   ├── test_config.py
│   └── test_connection.py
├── integration/
│   └── test_tools.py      # Tests with real/mock Mythic
└── contract/
    └── test_mcp_tools.py  # MCP protocol compliance
```

**Structure Decision**: Single project structure. This is an MCP server with no frontend, exposing tools via stdio transport. The `tools/` subdirectory groups related functionality but all tools are part of the core server (no plugins yet - that's a future feature per Constitution Principle III).

## Complexity Tracking

> No violations - design follows all constitution principles.

| Principle | Implementation Approach |
|-----------|------------------------|
| MCP Protocol First | FastMCP decorators auto-generate JSON-RPC |
| Async-Native | All tool functions are `async def` |
| Plugin Isolation | Tools are in separate modules, easily extractable |
| Explicit Authorization | Tool docstrings describe Mythic operations |
| Fail-Safe Defaults | Config validates credentials at import time |
