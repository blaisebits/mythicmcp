# Implementation Plan: Agent Plugin System

**Branch**: `003-agent-plugin-system` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-agent-plugin-system/spec.md`

## Summary

Implement a plugin system for MythicMCP that enables loading agent-specific tools (Apollo, Arachne, etc.) at startup. Each plugin defines tools for a specific Mythic agent type, which are namespaced (e.g., `apollo_shell`, `arachne_download`) and registered with the MCP server. Plugin tools execute commands on callbacks via the Mythic Python library's `issue_task` API with configurable timeouts.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0
**Storage**: N/A (stateless - plugins are Python modules loaded from filesystem)
**Testing**: pytest with pytest-asyncio for async tests
**Target Platform**: Linux/macOS/Windows (wherever Python runs)
**Project Type**: Single Python package
**Performance Goals**: Plugin loading <2s startup overhead per plugin (SC-002), tool execution <5s excluding Mythic task time (SC-001)
**Constraints**: Command timeout 30-300s configurable with 60s default (FR-010)
**Scale/Scope**: Initial release supports Apollo and Arachne agents, ~10 commands each (SC-003)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | ✅ PASS | Plugin tools registered as MCP tools via FastMCP decorator pattern |
| II. Async-Native Architecture | ✅ PASS | Plugin loading and task execution use async/await throughout |
| III. Plugin Isolation | ✅ PASS | This feature implements the plugin system mandated by the constitution |
| IV. Explicit Authorization Context | ✅ PASS | Tool descriptions state operations, agent type validation before execution (FR-004) |
| V. Fail-Safe Defaults | ✅ PASS | Malformed plugins logged and skipped (FR-006), unknown agent types rejected |

## Project Structure

### Documentation (this feature)

```text
specs/003-agent-plugin-system/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mythicmcp/
├── __init__.py
├── server.py            # FastMCP server - modified to load plugins
├── config.py            # Existing configuration
├── connection.py        # Existing Mythic connection
├── models.py            # Existing + new task/plugin models
├── tools/               # Existing core tools
│   ├── __init__.py
│   ├── callbacks.py
│   ├── operations.py
│   └── status.py
└── plugins/             # NEW - plugin system
    ├── __init__.py      # Plugin loader and registry
    ├── base.py          # BaseAgentPlugin abstract class
    ├── registry.py      # PluginRegistry for tool management
    ├── executor.py      # Task execution helper
    └── builtin/         # Bundled agent plugins
        ├── __init__.py
        ├── apollo.py    # Apollo agent plugin
        └── arachne.py   # Arachne agent plugin

tests/
├── unit/
│   ├── test_plugin_loader.py
│   ├── test_plugin_registry.py
│   └── test_executor.py
└── integration/
    └── test_plugin_tools.py
```

**Structure Decision**: Follows existing single-project structure. New `plugins/` subpackage contains the plugin system. Builtin plugins are bundled in `plugins/builtin/` for immediate availability.

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design completion.*

| Principle | Status | Design Validation |
|-----------|--------|-------------------|
| I. MCP Protocol First | ✅ PASS | All plugin tools use FastMCP `mcp.tool()` registration; responses are Pydantic models serialized as JSON-RPC |
| II. Async-Native Architecture | ✅ PASS | `issue_task()` and `get_all_task_output_by_id()` are async; all plugin handlers are async def |
| III. Plugin Isolation | ✅ PASS | `AgentPlugin` base class provides isolation; plugin failures caught in registry without crashing server |
| IV. Explicit Authorization Context | ✅ PASS | Tool descriptions in contracts specify operations; `AgentTypeMismatchError` validates callback compatibility |
| V. Fail-Safe Defaults | ✅ PASS | `PluginLoadError` logged but skipped; `timeout` parameter has bounds [30,300] with default 60; unknown agent types return error |

## Complexity Tracking

No constitution violations requiring justification.
