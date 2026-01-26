# Quickstart: Agent Plugin System

**Feature Branch**: `003-agent-plugin-system`
**Date**: 2026-01-26

## Overview

The Agent Plugin System extends MythicMCP with agent-specific tools for executing commands on Mythic callbacks. This guide covers using the bundled Apollo and Arachne plugins.

## Prerequisites

- MythicMCP installed and configured with Mythic credentials
- Active Mythic operation with callbacks
- Apollo or Arachne agents deployed

## Usage

### 1. Verify Plugins Loaded

After starting MythicMCP, verify plugins are loaded:

```
Tool: core_list_plugins

Response:
{
  "plugins": [
    {"agent_name": "apollo", "tool_count": 10, "supported_os": ["Windows"]},
    {"agent_name": "arachne", "tool_count": 8, "supported_os": ["Windows", "Linux"]}
  ],
  "total_count": 2
}
```

### 2. List Callbacks

Get callback IDs for targeting:

```
Tool: core_list_callbacks

Response:
{
  "callbacks": [
    {"id": 5, "hostname": "WORKSTATION01", "agent_type": "apollo", "active": true},
    {"id": 12, "hostname": "webserver", "agent_type": "arachne", "active": true}
  ]
}
```

### 3. Execute Commands

#### Apollo Shell Command

```
Tool: apollo_shell
Parameters:
  - callback_id: 5
  - command: "whoami"

Response:
{
  "success": true,
  "task_id": 42,
  "output": "WORKSTATION01\\admin"
}
```

#### Arachne Directory Listing

```
Tool: arachne_ls
Parameters:
  - callback_id: 12
  - path: "/var/www/html"

Response:
{
  "success": true,
  "task_id": 43,
  "output": "index.php\nconfig.php\nuploads/"
}
```

### 4. Handle Agent Type Mismatches

If you call the wrong tool for a callback's agent type:

```
Tool: apollo_shell
Parameters:
  - callback_id: 12  # This is an arachne callback!
  - command: "whoami"

Response:
{
  "success": false,
  "error": "Agent type mismatch: tool requires 'apollo' but callback 12 is 'arachne'",
  "error_type": "agent_mismatch"
}
```

Use `arachne_shell` instead for Arachne callbacks.

## Available Tools

### Apollo Tools (Windows)

| Tool | Description |
|------|-------------|
| `apollo_shell` | Execute cmd.exe command |
| `apollo_execute_assembly` | Run .NET assembly |
| `apollo_download` | Download file |
| `apollo_pwd` | Get working directory |
| `apollo_ls` | List directory |
| `apollo_cd` | Change directory |
| `apollo_cat` | Read file |
| `apollo_ps` | List processes |
| `apollo_run` | Execute program |
| `apollo_screenshot` | Capture screenshot |

### Arachne Tools (Windows/Linux)

| Tool | Description |
|------|-------------|
| `arachne_shell` | Execute command |
| `arachne_download` | Download file |
| `arachne_upload` | Upload file |
| `arachne_pwd` | Get working directory |
| `arachne_ls` | List directory |
| `arachne_cd` | Change directory |
| `arachne_rm` | Remove file |
| `arachne_execute_assembly` | Run .NET assembly (ASPX only) |

## Timeouts

All commands support a `timeout` parameter (30-300 seconds, default 60):

```
Tool: apollo_execute_assembly
Parameters:
  - callback_id: 5
  - assembly_name: "Seatbelt.exe"
  - assembly_arguments: "-group=all"
  - timeout: 180  # 3 minutes for long-running assembly
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `agent_mismatch` | Wrong tool for callback type | Use correct agent prefix |
| `callback_not_found` | Invalid callback ID | Use `core_list_callbacks` |
| `callback_inactive` | Callback disconnected | Target active callback |
| `timeout` | Command took too long | Increase timeout parameter |
| `no_operation` | No Mythic operation set | Set operation in Mythic UI |

## Creating Custom Plugins

See `src/mythicmcp/plugins/builtin/apollo.py` for an example plugin implementation.

```python
from mythicmcp.plugins.base import AgentPlugin, ToolDefinition
from pydantic import BaseModel, Field

class MyAgentShellParams(BaseModel):
    callback_id: int
    command: str
    timeout: int = 60

class MyAgentPlugin(AgentPlugin):
    agent_name = "myagent"
    agent_description = "My custom agent"
    supported_os = ["Windows", "Linux"]

    def get_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="shell",
                description="Execute shell command",
                parameters=MyAgentShellParams,
                handler=self._shell_handler,
            )
        ]

    async def _shell_handler(self, ctx, params: MyAgentShellParams):
        # Implementation here
        pass
```

Place in `src/mythicmcp/plugins/builtin/` for bundled plugins.
