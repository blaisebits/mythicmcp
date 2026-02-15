# Contract: YAML Agent Configuration Schema

**Feature**: 006-yaml-plugin-config
**Date**: 2026-02-15

## YAML Configuration File Contract

Each agent plugin is defined by a single YAML file with this structure.

### Top-Level Structure

```yaml
# Required: Agent metadata
agent:
  name: <string>           # Required. Lowercase alphanumeric + hyphens, 1-50 chars
  description: <string>    # Required. Human-readable description
  supported_os:             # Required. At least one entry
    - <string>             # "Windows" | "Linux" | "macOS"

# Required: Command definitions
commands:
  - <CommandDef>           # At least one command required
```

### CommandDef Structure

```yaml
- name: <string>            # Required. Lowercase alphanumeric + underscores, 1-50 chars
  description: <string>     # Required. User-facing tool description
  mythic_command: <string>  # Optional. Defaults to `name` if omitted
  timeout: <integer>        # Optional. Default: 60. Range: 30-300
  parameters:               # Optional. Defaults to empty list
    - <ParameterDef>
```

### ParameterDef Structure

```yaml
- name: <string>            # Required. Valid Python identifier
  type: <string>            # Required. "string" | "integer" | "boolean"
  description: <string>     # Required. User-facing description
  required: <boolean>       # Optional. Default: true
  default: <any>            # Optional. Must match declared type
  role: <string>            # Optional. "task" | "meta". Default: "task"
  min: <integer>            # Optional. Integer type only
  max: <integer>            # Optional. Integer type only
  choices:                  # Optional. String type only
    - <string>
```

### Implicit Parameters (not in YAML)

Every command automatically receives:

| Name        | Type    | Required | Default          | Role |
| ----------- | ------- | -------- | ---------------- | ---- |
| callback_id | integer | yes      | —                | meta |
| timeout     | integer | no       | command's timeout | meta |

### Type Mapping

| YAML Type   | Python Type | Pydantic Field |
| ----------- | ----------- | -------------- |
| "string"    | str         | Field(...)     |
| "integer"   | int         | Field(...)     |
| "boolean"   | bool        | Field(...)     |

## Generated Tool Contract

For each command defined in the config, the system generates an MCP tool with:

- **Tool name**: `{agent.name}_{command.name}` (e.g., `apollo_shell`)
- **Tool description**: `command.description`
- **Parameters**: `callback_id` + command parameters + `timeout`
- **Return type**: `PluginToolSuccessResponse | PluginToolErrorResponse`

### Generated Handler Behavior

```
1. Extract callback_id from params
2. Extract timeout from params (use command default if not provided)
3. Collect all task-role parameters into dict
4. Call execute_with_validation(ctx, callback_id, agent.name, command.mythic_command, params_dict, timeout)
5. Return result
```

## Validation Error Contract

When a config file fails validation, the error includes:

```
{
  "file": "<absolute path to YAML file>",
  "agent": "<agent name if parseable, else 'unknown'>",
  "errors": [
    {
      "field": "<dotted path, e.g., 'commands[0].parameters[1].type'>",
      "message": "<human-readable error>"
    }
  ]
}
```

The plugin is skipped; other plugins continue loading.
