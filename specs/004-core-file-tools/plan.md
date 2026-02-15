# Implementation Plan: Core File Management Tools

**Branch**: `004-core-file-tools` | **Date**: 2026-02-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-core-file-tools/spec.md`

## Summary

Implement four core MCP tools for file management on the Mythic server: `core_upload_file`, `core_download_file`, `core_list_downloaded_files`, and `core_list_uploaded_files`. These tools wrap the existing Mythic Python API functions (`register_file`, `download_file`, `get_all_downloaded_files`, `get_all_uploaded_files`) and expose them through the MCP protocol with base64-encoded file content transport.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0
**Storage**: N/A (stateless - files stored on Mythic server)
**Testing**: pytest with integration tests against Mythic instance
**Target Platform**: Linux server (same as existing MythicMCP)
**Project Type**: Single project (extends existing MCP server)
**Performance Goals**: 5s upload for <10MB files, 50MB download without timeout (SC-001, SC-002)
**Constraints**: Base64 encoding for MCP transport, operation-scoped file access
**Scale/Scope**: Up to 1000 files per operation, 50MB max file size

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | ✅ PASS | All file tools exposed via MCP @tool decorators |
| II. Async-Native Architecture | ✅ PASS | Uses async Mythic Python API functions |
| III. Plugin Isolation | ✅ PASS | Core tools, not agent-specific (belongs in server.py/tools/) |
| IV. Explicit Authorization Context | ✅ PASS | Tools require operation context, clear descriptions |
| V. Fail-Safe Defaults | ✅ PASS | Returns errors for missing files, connection issues |

## Project Structure

### Documentation (this feature)

```text
specs/004-core-file-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/mythicmcp/
├── server.py            # Add 4 new tool definitions
├── models.py            # Add file-related Pydantic models
├── tools/
│   ├── __init__.py
│   ├── callbacks.py
│   ├── operations.py
│   ├── status.py
│   └── files.py         # NEW: File tool implementations
└── ...

tests/
├── integration/
│   └── test_file_tools.py  # NEW: Integration tests for file tools
└── ...
```

**Structure Decision**: Follows existing pattern where tool implementations live in `src/mythicmcp/tools/` and are registered in `server.py`. File tools are core functionality (not agent-specific) so they belong in the tools directory, not plugins.

## Complexity Tracking

> No violations requiring justification. Implementation follows existing patterns.
