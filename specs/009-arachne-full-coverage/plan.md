# Implementation Plan: Arachne Full Command Coverage

**Branch**: `009-arachne-full-coverage` | **Date**: 2026-03-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-arachne-full-coverage/spec.md`

## Summary

Fix parameter mismatches in 3 Arachne YAML commands (download, upload, execute_assembly), correct platform restriction descriptions for 2 commands (cd, execute_assembly), and add agent version metadata. Single YAML file change — no Python code modifications needed.

## Technical Context

**Language/Version**: Python 3.10+ (no code changes; YAML config only)
**Primary Dependencies**: pyyaml>=6.0.0 (existing), yaml_loader.py (existing)
**Storage**: N/A (stateless — config file read at startup)
**Testing**: pytest, integration tests against live Mythic instance
**Target Platform**: MCP server (Linux/macOS/Windows host)
**Project Type**: single
**Performance Goals**: N/A (config change, no runtime impact)
**Constraints**: Parameter names must exactly match Mythic agent source
**Scale/Scope**: 1 file modified, 5 commands updated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | Tools remain valid MCP tools; parameter names change but JSON-RPC format preserved |
| II. Async-Native Architecture | PASS | No code changes; executor remains async |
| III. Plugin Isolation | PASS | Change is within Arachne plugin YAML only; no core server changes |
| IV. Explicit Authorization Context | PASS | Tool descriptions updated to clearly state file_id requirements and platform restrictions |
| V. Fail-Safe Defaults | PASS | Required parameters remain required; optional parameters have defaults |

**Post-design re-check**: All gates still pass. YAML-only change has no architectural impact.

## Project Structure

### Documentation (this feature)

```text
specs/009-arachne-full-coverage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── yaml-parameter-schema.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/mythicmcp/plugins/builtin/
└── arachne.yaml         # Only file modified

tests/
├── unit/
│   └── test_yaml_loader.py  # Verify corrected YAML loads without errors
└── integration/
    └── config.arachne.yaml  # Update test config for corrected params
```

**Structure Decision**: Minimal change — single YAML file in existing plugin directory. No new files, directories, or modules needed. Unit tests validate YAML loading; integration tests validate against live Mythic.
