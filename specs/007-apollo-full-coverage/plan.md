# Implementation Plan: Apollo Full Command Coverage

**Branch**: `007-apollo-full-coverage` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-apollo-full-coverage/spec.md`

## Summary

Expand apollo.yaml from 10 to 62 commands (100% of Apollo 2.4.8) and add a `metadata` top-level field to the YAML config schema for version tracking. Three files change: apollo.yaml (add 52 commands + metadata), yaml_loader.py (add metadata field), test_yaml_loader.py (update assertions).

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0
**Storage**: N/A (stateless — YAML config files read at startup)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server
**Project Type**: Single project
**Performance Goals**: N/A (startup-time config loading only)
**Constraints**: YAML parameter types limited to string, integer, boolean
**Scale/Scope**: 62 command definitions in one YAML file, ~1 line change in yaml_loader.py

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | All commands exposed as MCP tools via existing plugin system |
| II. Async-Native | PASS | Handlers use async execute_with_validation, no change needed |
| III. Plugin Isolation | PASS | Changes scoped to Apollo plugin YAML + shared YAML loader |
| IV. Explicit Authorization | PASS | Tool descriptions state what operations are performed |
| V. Fail-Safe Defaults | PASS | Timeouts set per command, validation at startup |

No violations. Re-check after Phase 1: PASS (no architectural changes, data-only expansion).

## Project Structure

### Documentation (this feature)

```text
specs/007-apollo-full-coverage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── yaml-metadata-schema.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/mythicmcp/plugins/
├── builtin/
│   └── apollo.yaml          # Expand from 10 → 62 commands, add metadata
├── yaml_loader.py           # Add metadata field to YamlConfigModel
└── ...

tests/unit/
└── test_yaml_loader.py      # Update tool count assertions, add metadata tests
```

**Structure Decision**: Single project, existing layout. No new files or directories needed.
