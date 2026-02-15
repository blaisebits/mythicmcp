# Quickstart: YAML-Driven Agent Plugin Configuration

**Feature**: 006-yaml-plugin-config
**Date**: 2026-02-15

## Overview

This feature replaces code-based agent plugin definitions with YAML configuration files. Each agent's commands, parameters, and metadata are defined in a single `.yaml` file instead of a Python module.

## Creating a New Agent Plugin

### 1. Create the YAML file

Place a `.yaml` file in the plugins directory (builtin or external):

```yaml
# src/mythicmcp/plugins/builtin/myagent.yaml
agent:
  name: myagent
  description: "My custom Mythic agent"
  supported_os:
    - Linux
    - Windows

commands:
  - name: shell
    description: "Execute a shell command on a myagent callback"
    timeout: 60
    parameters:
      - name: command
        type: string
        description: "Shell command to execute"
        required: true

  - name: whoami
    description: "Get current user identity on a myagent callback"
    timeout: 30
```

### 2. Restart the server

The new tools (`myagent_shell`, `myagent_whoami`) are available immediately.

### 3. Verify

```
core_list_plugins → shows "myagent" with 2 tools
myagent_shell(callback_id=1, command="id") → executes on target
```

## Parameter Types and Constraints

```yaml
parameters:
  # Required string parameter
  - name: command
    type: string
    description: "Command to run"
    required: true

  # Optional string with default
  - name: path
    type: string
    description: "Target path"
    default: "."

  # Integer with range constraints
  - name: count
    type: integer
    description: "Number of results"
    default: 10
    min: 1
    max: 100

  # Boolean parameter
  - name: recursive
    type: boolean
    description: "Search recursively"
    default: false
```

## Migrated Apollo Example

The Apollo agent's 10 tools are defined in `apollo.yaml`:

```yaml
agent:
  name: apollo
  description: "Apollo Windows C# agent"
  supported_os:
    - Windows

commands:
  - name: shell
    description: "Execute a shell command via cmd.exe on an Apollo callback"
    mythic_command: shell
    timeout: 60
    parameters:
      - name: command
        type: string
        description: "Shell command to execute via cmd.exe"
        required: true

  - name: run
    description: "Execute a program without cmd.exe wrapper on an Apollo callback"
    mythic_command: run
    timeout: 60
    parameters:
      - name: executable
        type: string
        description: "Path to executable"
        required: true
      - name: arguments
        type: string
        description: "Arguments to pass to executable"
        default: ""

  - name: download
    description: "Download a file from an Apollo callback"
    mythic_command: download
    timeout: 120
    parameters:
      - name: path
        type: string
        description: "Path to file to download"
        required: true
```

## Validation Scenarios

| Scenario                  | Expected Behavior                                           |
| ------------------------- | ----------------------------------------------------------- |
| Valid YAML config         | Agent loads, tools registered, appears in core_list_plugins |
| Missing `agent.name`      | Error logged with file path, plugin skipped                 |
| Duplicate command names   | Error logged identifying duplicates, plugin skipped         |
| Invalid parameter type    | Error logged identifying command and field, plugin skipped  |
| Unrecognized top-level key | Warning logged, plugin loads successfully                   |
| Empty commands list       | Warning logged, plugin loads with no tools                  |

## Troubleshooting

| Error                     | Cause                        | Solution                                 |
| ------------------------- | ---------------------------- | ---------------------------------------- |
| Agent not appearing       | YAML file not in plugins dir | Check file location and extension        |
| Parameter validation fail | Constraint mismatch          | Check min/max/type match the value       |
| "Unknown agent type"      | Callback agent != config name | Verify agent name matches Mythic payload |
| Tool not executing        | mythic_command mismatch      | Verify mythic_command matches agent cmd  |
