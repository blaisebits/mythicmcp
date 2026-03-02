# Implementation Plan: Poseidon Agent Built-in Plugin

**Branch**: `008-poseidon-plugin` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-poseidon-plugin/spec.md`

## Summary

Add a YAML-defined Poseidon agent plugin covering all ~76 Poseidon 2.2.8 commands for macOS/Linux targets. Follows the identical pattern established by the Apollo YAML plugin — no loader changes required. Deliverables: `poseidon.yaml`, unit tests, integration test sample config entries.

## Technical Context

**Language/Version**: Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0
**Primary Dependencies**: Existing YAML loader (`yaml_loader.py`), plugin base classes, executor
**Storage**: N/A (stateless — YAML config files read at startup)
**Testing**: pytest, pytest-asyncio (unit), live Mythic integration tests
**Target Platform**: MCP server (Linux/macOS host connecting to Mythic server)
**Project Type**: Single project
**Performance Goals**: N/A (stateless tool registration at startup)
**Constraints**: No changes to the YAML loader; poseidon.yaml must validate against existing Pydantic models
**Scale/Scope**: ~76 command definitions in YAML, ~76 MCP tools generated at startup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | All tools exposed as MCP tools via standard YAML loader |
| II. Async-Native Architecture | PASS | Handlers use `execute_with_validation` which is async |
| III. Plugin Isolation | PASS | Poseidon is a separate YAML plugin; core server untouched |
| IV. Explicit Authorization Context | PASS | Tool descriptions describe Mythic operations; destructive ops labeled |
| V. Fail-Safe Defaults | PASS | YAML validation at startup; invalid config prevents plugin load |
| Security & Authorization | PASS | No credentials in YAML; Mythic auth handled by core |
| MCP Protocol Compliance | PASS | Standard tool registration via plugin system |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/008-poseidon-plugin/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/mythicmcp/plugins/builtin/
├── apollo.yaml          # Existing — 78 commands
├── arachne.yaml         # Existing — 8 commands
└── poseidon.yaml        # NEW — ~76 commands

tests/unit/
└── test_yaml_loader.py  # MODIFY — add Poseidon load/count tests

tests/integration/
└── config.sample.yaml   # MODIFY — add Poseidon test commands section
```

**Structure Decision**: Single new YAML file + test modifications. No new Python modules, no new directories.
