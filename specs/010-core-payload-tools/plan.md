# Implementation Plan: Core Payload Tools

**Branch**: `010-core-payload-tools` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-core-payload-tools/spec.md`

## Summary

Add 6 new core MCP tools for managing Mythic payloads: list, get detail, create, download, check config, and get redirect rules. Follows established patterns from `files.py` and `callbacks.py` — new `payloads.py` module with Pydantic response models, typed exceptions, and `@mcp.tool()` registration.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0 (all existing)
**Storage**: N/A (stateless — queries Mythic server)
**Testing**: pytest, pytest-asyncio (existing)
**Target Platform**: Linux server (MCP server process)
**Project Type**: single
**Performance Goals**: N/A (proxies to Mythic API; payload builds are inherently slow)
**Constraints**: Build timeout default 300s, max 600s. JSON string params for complex inputs (MCP tool limitation).
**Scale/Scope**: Returns all payloads in operation (no pagination). Payload binaries returned as base64.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. MCP Protocol First | PASS | All 6 tools exposed as MCP tools with JSON-RPC responses |
| II. Async-Native Architecture | PASS | All functions async, uses `mythic` library async functions |
| III. Plugin Isolation | PASS | Core tools, not agent-specific. No agent logic in tool module |
| IV. Explicit Authorization Context | PASS | Tool descriptions clearly state operations. Create payload is labeled. Timeout defaults prevent silent waiting |
| V. Fail-Safe Defaults | PASS | 300s default timeout, empty string validation, operation-required checks, no silent failures |

**Post-design re-check**: All gates still pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-core-payload-tools/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── payload-tools.md # MCP tool contracts
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/mythicmcp/
├── tools/
│   ├── __init__.py          # Modified: add payload tool exports
│   ├── payloads.py          # NEW: 6 payload tools + exceptions + parsers
│   ├── callbacks.py         # Existing (reference pattern)
│   ├── files.py             # Existing (reference pattern)
│   ├── operations.py        # Existing (reference pattern)
│   └── status.py            # Existing
├── models.py                # Modified: add payload response models
└── server.py                # Modified: register 6 payload tools

tests/unit/
└── test_payload_tools.py    # NEW: unit tests
```

**Structure Decision**: Single new module `payloads.py` in existing `tools/` directory, matching the flat structure of `callbacks.py`, `files.py`, `operations.py`. No new directories needed.
