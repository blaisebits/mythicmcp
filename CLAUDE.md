# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MythicMCP is an MCP (Model Context Protocol) server for the Mythic C2 Framework. It provides programmatic access to Mythic operations with a plugin system for agent-specific interactions.

## Reference Materials

The `/refs/` directory contains reference implementations (gitignored, not part of main project):
- `refs/Mythic-3.4.0.5/` - Mythic core framework (Go backend, React UI, Docker containers)
- `refs/Mythic_Scripting/` - Python async scripting library (`pip install mythic`)
- `refs/agents/` - Reference agents (Apollo/C#, Arachne/Go, Poseidon)

Each reference has its own CLAUDE.md with detailed architecture notes. Consult these when implementing Mythic integrations.

## Mythic Python API Patterns

The MCP server will wrap the `mythic` Python package. Key patterns:

```python
from mythic import mythic

# All functions are async - must be awaited
mythic_instance = await mythic.login(server_ip="...", username="...", password="...")

# All API calls take mythic_instance as first parameter
callbacks = await mythic.get_all_active_callbacks(mythic_instance)

# Custom GraphQL for operations not in built-in functions
result = await mythic.execute_custom_query(mythic_instance, query, variables)
```

## Development Workflow

This project uses the Specify framework for structured development. Key commands:

| Command | Purpose |
|---------|---------|
| `/speckit.specify` | Create feature specification |
| `/speckit.clarify` | Ask clarification questions on specs |
| `/speckit.plan` | Generate implementation plan |
| `/speckit.tasks` | Generate actionable task list |
| `/speckit.implement` | Execute implementation |
| `/speckit.analyze` | Cross-artifact consistency check |

Features are developed on branches named `feature/<name>`. Artifacts are stored in `.specify/features/<branch-name>/`.

## Key Directories

- `.specify/templates/` - Templates for specs, plans, tasks
- `.specify/memory/` - Project constitution and shared context
- `.specify/features/` - Per-feature planning artifacts
- `.claude/commands/` - Speckit command definitions

## Active Technologies
- Python 3.10+ + mcp (1.26.0+), mythic (0.2.10+), pydantic (001-mythic-core-tools)
- N/A (stateless - queries Mythic server) (001-mythic-core-tools)

## Recent Changes
- 001-mythic-core-tools: Added Python 3.10+ + mcp (1.26.0+), mythic (0.2.10+), pydantic
