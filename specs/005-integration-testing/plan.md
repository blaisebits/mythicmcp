# Implementation Plan: Integration Testing Pipeline

**Branch**: `005-integration-testing` | **Date**: 2026-02-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-integration-testing/spec.md`

## Summary

Add an end-to-end integration testing pipeline that generates Mythic agent payloads, downloads them, uploads them to target systems (Debian Linux, Windows 11) via existing callbacks, executes them, verifies new callbacks appear, and runs test commands. All test configuration is driven from a self-contained YAML file (`tests/integration/config.yaml`). Tests are structured as separate phases per agent/target pair with dependency-based skipping, and full cleanup (payload removal + callback deactivation) runs after each test pipeline.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pytest, pytest-asyncio, pyyaml, pydantic, mythic (0.2.10+)
**Storage**: N/A (stateless — tests interact with Mythic server and target systems)
**Testing**: pytest with `asyncio_mode = "auto"`, `@pytest.mark.integration` marker
**Target Platform**: Linux (test runner), targeting Debian Linux and Windows 11 systems
**Project Type**: Single project — test code lives in `tests/integration/`
**Performance Goals**: N/A (test suite, not production service)
**Constraints**: Tests require a running Mythic server and reachable target systems with pre-existing callbacks
**Scale/Scope**: 2 target systems, 2+ agent types (Apollo, Arachne), ~20 test functions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | **N/A** | This feature adds tests, not MCP tools. Tests validate MCP tool behavior indirectly. |
| II. Async-Native Architecture | **PASS** | All test code uses async/await via pytest-asyncio. Mythic API calls are async. |
| III. Plugin Isolation | **PASS** | Tests use existing plugins (Apollo, Arachne) without modifying core or plugin code. |
| IV. Explicit Authorization Context | **PASS** | Tests use YAML-configured credentials. No implicit or hardcoded credentials in test code. |
| V. Fail-Safe Defaults | **PASS** | Missing config skips tests gracefully. Timeouts have defaults (120s callback, 60s commands). Unknown agents rejected during config validation. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-integration-testing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (YAML config schema)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (test helper API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
tests/
├── integration/
│   ├── config.sample.yaml       # Committed sample config with placeholders
│   ├── config.yaml              # Gitignored — operator's real config
│   ├── conftest.py              # Integration test fixtures (config loading, Mythic connection)
│   ├── test_payload_generation.py   # US2: payload build + download tests
│   ├── test_payload_deployment.py   # US3: upload + execute on targets
│   ├── test_callback_verification.py # US4: poll for new callbacks
│   ├── test_command_execution.py     # US5: run commands + validate output
│   └── test_cleanup.py              # Cleanup verification tests
├── unit/
│   ├── test_integration_config.py   # US1: YAML config loading + validation
│   └── ... (existing unit tests)
└── conftest.py                  # Existing root conftest
```

**Structure Decision**: Tests live in the existing `tests/` directory. YAML config parsing models live in `tests/integration/conftest.py` (or a small helper module) since they are test-only code — not part of the MythicMCP package itself. The config sample file is committed; the real config is gitignored.

## Complexity Tracking

No constitution violations to justify.
