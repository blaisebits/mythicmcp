# Data Model: YAML-Driven Agent Plugin Configuration

**Feature**: 006-yaml-plugin-config
**Date**: 2026-02-15

## Entities

### AgentConfig

Represents a complete agent plugin definition loaded from a single YAML file.

| Field          | Type             | Required | Description                                      |
| -------------- | ---------------- | -------- | ------------------------------------------------ |
| name           | string           | Yes      | Agent identifier (lowercase, e.g., "apollo")     |
| description    | string           | Yes      | Human-readable agent description                 |
| supported_os   | list[string]     | Yes      | Supported platforms (e.g., ["Windows"])           |
| commands       | list[CommandDef] | Yes      | Available commands (at least one)                 |

**Validation Rules**:
- `name` must be lowercase alphanumeric with optional hyphens, 1-50 characters
- `name` must not conflict with other loaded agents
- `supported_os` values must be from: "Windows", "Linux", "macOS"
- `commands` must contain at least one entry
- `commands` must have unique names within the agent

### CommandDef

Represents a single command within an agent configuration.

| Field          | Type              | Required | Default        | Description                                        |
| -------------- | ----------------- | -------- | -------------- | -------------------------------------------------- |
| name           | string            | Yes      | —              | Command name (e.g., "shell")                       |
| description    | string            | Yes      | —              | User-facing tool description                       |
| mythic_command | string            | No       | same as `name` | Mythic-side command name if different from `name`   |
| timeout        | integer           | No       | 60             | Default timeout in seconds                         |
| parameters     | list[ParameterDef]| No       | []             | Command parameters (beyond implicit callback_id)   |

**Validation Rules**:
- `name` must be lowercase alphanumeric with optional underscores, 1-50 characters
- `name` must not be a reserved word: "ctx", "context", "self"
- `timeout` must be between 30 and 300
- `description` must not be empty

### ParameterDef

Represents a single parameter for a command.

| Field       | Type          | Required | Default  | Description                                      |
| ----------- | ------------- | -------- | -------- | ------------------------------------------------ |
| name        | string        | Yes      | —        | Parameter name (e.g., "command", "path")         |
| type        | string        | Yes      | —        | Type: "string", "integer", or "boolean"          |
| description | string        | Yes      | —        | User-facing parameter description                |
| required    | boolean       | No       | true     | Whether the parameter is required                |
| default     | any           | No       | —        | Default value (makes parameter optional)         |
| role        | string        | No       | "task"   | "task" (sent to Mythic) or "meta" (local)        |
| min         | integer       | No       | —        | Minimum value (integer type only)                |
| max         | integer       | No       | —        | Maximum value (integer type only)                |
| choices     | list[string]  | No       | —        | Allowed values (string type only)                |

**Validation Rules**:
- `name` must be a valid Python identifier
- `name` must not be "callback_id" or "timeout" (these are implicit)
- `type` must be one of: "string", "integer", "boolean"
- `default` must match the declared `type`
- `min`/`max` only valid for `type: "integer"`
- `choices` only valid for `type: "string"`
- `role` must be one of: "task", "meta"
- If `default` is provided, `required` is implicitly false

### Implicit Parameters

Every command automatically includes these parameters (not declared in YAML):

| Parameter    | Type    | Required | Default | Role | Description                     |
| ------------ | ------- | -------- | ------- | ---- | ------------------------------- |
| callback_id  | integer | Yes      | —       | meta | Callback ID to execute on       |
| timeout      | integer | No       | (from command def) | meta | Timeout in seconds   |

These are injected by the config loader and do not appear in the YAML file.

## Entity Relationships

```
AgentConfig (1) ──contains──> (1..*) CommandDef
CommandDef  (1) ──contains──> (0..*) ParameterDef
CommandDef  (1) ──has──>      (2)    Implicit Parameters (callback_id, timeout)
```

## State Transitions

AgentConfig loading follows this lifecycle:

```
YAML File → Parse → Validate → Build Pydantic Models → Generate Handlers → Register in Plugin Registry
```

1. **Parse**: YAML file read and parsed via safe_load
2. **Validate**: Pydantic config models validate structure and constraints
3. **Build**: Dynamic Pydantic parameter models created from ParameterDef + implicit params
4. **Generate**: Handler functions created that call execute_with_validation
5. **Register**: Plugin and tools added to PluginRegistry via existing interface

## Example YAML

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

  - name: pwd
    description: "Get current working directory of an Apollo callback"
    mythic_command: pwd
    timeout: 60

  - name: ls
    description: "List directory contents on an Apollo callback"
    mythic_command: ls
    timeout: 60
    parameters:
      - name: path
        type: string
        description: "Path to list (default: current directory)"
        required: false
        default: "."
```
