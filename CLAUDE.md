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
- Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, hatchling (build) (002-uv-tool-install)
- N/A (stateless - plugins are Python modules loaded from filesystem) (003-agent-plugin-system)

## Installation

Install as a global tool using uv:

```bash
uv tool install mythicmcp
```

The `mythicmcp` command will be available in your PATH after installation.

## Error Handling Pattern

Configuration errors display user-friendly guidance instead of stack traces. The pattern in `server.py`:

```python
try:
    mcp.run()
except ExceptionGroup as eg:
    # FastMCP wraps errors in ExceptionGroup - extract and handle
    for exc in eg.exceptions:
        if isinstance(exc, ConfigurationError):
            print(CONFIGURATION_GUIDANCE, file=sys.stderr)
            sys.exit(1)
    raise
```

## Plugin System

The plugin system allows agent-specific tools to be loaded dynamically. Plugins are located in:
- `src/mythicmcp/plugins/builtin/` - Bundled plugins (Apollo, Arachne)
- External directory via `MYTHICMCP_PLUGINS_DIR` environment variable

### Creating a Plugin

```python
from mythicmcp.plugins.base import AgentPlugin, ToolDefinition
from pydantic import BaseModel, Field

class MyToolParams(BaseModel):
    callback_id: int = Field(..., description="Target callback")
    command: str = Field(..., description="Command to run")

class MyAgentPlugin(AgentPlugin):
    agent_name = "myagent"
    agent_description = "My custom agent"
    supported_os = ["Windows", "Linux"]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="shell",
                description="Execute shell command",
                parameters=MyToolParams,
                handler=self._shell_handler,
            )
        ]

    async def _shell_handler(self, ctx, params):
        from mythicmcp.plugins.executor import execute_with_validation
        return await execute_with_validation(
            ctx, params.callback_id, "myagent", "shell",
            {"command": params.command}
        )
```

### Available Plugins

- **Apollo** (10 tools): shell, pwd, ls, cd, cat, ps, run, download, execute_assembly, screenshot
- **Arachne** (8 tools): shell, pwd, ls, cd, rm, download, upload, execute_assembly

## Recent Changes
- 003-agent-plugin-system: Added plugin system with Apollo (10 tools) and Arachne (8 tools) plugins, dynamic tool loading, agent type validation
- 001-mythic-core-tools: Added Python 3.10+ + mcp (1.26.0+), mythic (0.2.10+), pydantic
- 002-uv-tool-install: Added uv tool installation support, user-friendly startup errors, comprehensive README
