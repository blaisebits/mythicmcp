# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
Reponses should be concise, sacrafice grammar for the sace of consicsion.

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
- N/A (stateless - files stored on Mythic server) (004-core-file-tools)
- Python 3.10+ + pytest, pytest-asyncio, pyyaml, pydantic, mythic (0.2.10+) (005-integration-testing)
- N/A (stateless — tests interact with Mythic server and target systems) (005-integration-testing)
- Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0 (006-yaml-plugin-config)
- N/A (stateless — config files read at startup) (006-yaml-plugin-config)
- N/A (stateless — YAML config files read at startup) (007-apollo-full-coverage)
- Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0 + Existing YAML loader (`yaml_loader.py`), plugin base classes, executor (008-poseidon-plugin)

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

The plugin system allows agent-specific tools to be loaded dynamically. Plugins can be defined via YAML configuration files (preferred) or Python code (for advanced use cases). Plugins are located in:
- `src/mythicmcp/plugins/builtin/` - Bundled plugins (Apollo, Poseidon, Arachne via YAML)
- External directory via `MYTHICMCP_PLUGINS_DIR` environment variable

YAML configs are loaded first, then Python modules. If both define the same agent name, the YAML version takes precedence.

### Creating a Plugin via YAML (Preferred)

Place a `.yaml` file in the plugins directory:

```yaml
# src/mythicmcp/plugins/builtin/myagent.yaml
agent:
  name: myagent
  description: "My custom agent"
  supported_os:
    - Windows
    - Linux

commands:
  - name: shell
    description: "Execute a shell command on a myagent callback"
    mythic_command: shell
    timeout: 60
    parameters:
      - name: command
        type: string
        description: "Shell command to execute"
        required: true

  - name: status
    description: "Get agent status on a myagent callback"
    timeout: 30
```

Supported parameter types: `string`, `integer`, `boolean`. Parameters support `required`, `default`, `min`/`max` (integers), and `choices` (strings). The `callback_id` and `timeout` parameters are implicit.

The YAML loader (`src/mythicmcp/plugins/yaml_loader.py`) validates configs at startup using Pydantic models and auto-generates tool handlers that call `execute_with_validation()`.

### Creating a Plugin via Python (Advanced)

For commands requiring custom handler logic:

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

- **Apollo** (78 tools, YAML-defined): Full coverage of Apollo 2.4.8 — shell, powershell, powerpick, ls, cat, download, upload, execute_assembly, mimikatz, and 69 more
- **Poseidon** (74 tools, YAML-defined): Full coverage of Poseidon 2.2.8 (macOS/Linux) — shell, pty, run, ls, cat, download, upload, curl, portscan, sshauth, XPC, and 63 more
- **Arachne** (8 tools, YAML-defined): shell, pwd, ls, cd, rm, download, upload, execute_assembly

## Core Tools

The MCP server exposes these core tools for Mythic operations:

### Callback Tools
- `core_list_callbacks` - List all active callbacks in current operation
- `core_get_callback` - Get detailed callback information by ID

### Operation Tools
- `core_list_operations` - List all accessible operations
- `core_set_operation` - Set current operation context
- `core_get_operation` - Get operation details

### Status Tools
- `core_check_connection` - Verify Mythic server connectivity
- `core_list_plugins` - List loaded agent plugins

### File Tools
- `core_upload_file` - Upload file to Mythic for agent tasking (returns file_id)
- `core_download_file` - Download file from Mythic by UUID (base64-encoded content)
- `core_list_downloaded_files` - List files downloaded from agents
- `core_list_uploaded_files` - List files uploaded to Mythic

## Recent Changes
- 008-poseidon-plugin: Added Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0 + Existing YAML loader (`yaml_loader.py`), plugin base classes, executor
- 007-apollo-full-coverage: Added Python 3.10+ + mcp>=1.26.0, mythic>=0.2.10, pydantic>=2.0.0, pyyaml>=6.0.0
- 006-yaml-plugin-config: YAML-driven plugin config system. apollo.yaml replaces apollo.py, new yaml_loader.py module, pyyaml added to main dependencies. Plugins can now be defined via YAML without writing Python code.
