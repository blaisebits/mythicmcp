# YAML Plugin Contract: Poseidon

## Schema

The `poseidon.yaml` file MUST conform to the `YamlConfigModel` schema defined in `src/mythicmcp/plugins/yaml_loader.py`. No extensions or custom fields beyond what the loader supports.

## Required Top-Level Keys

```yaml
agent:
  name: poseidon                          # lowercase, alphanumeric + hyphens
  description: "..."                      # non-empty
  supported_os: [macOS, Linux]            # from: Windows, Linux, macOS

metadata:                                 # optional but recommended
  agent_version: "2.2.8"
  mythic_version: "3.3.0+"

commands:                                 # at least 1 command
  - name: <command_name>                  # lowercase, alphanumeric + underscores
    description: "..."                    # non-empty
    mythic_command: <mythic_name>         # optional, defaults to name
    timeout: 60                           # 30-300
    parameters: []                        # optional list
```

## Parameter Contract

Each parameter MUST have:
- `name`: valid Python identifier, not in reserved set (callback_id, timeout, ctx, context, self)
- `type`: one of "string", "integer", "boolean"
- `description`: non-empty string

Optional fields:
- `required`: boolean (default: true)
- `default`: must match declared type
- `choices`: list of strings (string type only)
- `min`/`max`: integers (integer type only)

## Implicit Parameters

The YAML loader automatically adds to every command:
- `callback_id` (int, required) — first parameter
- `timeout` (int, optional, default from command config) — last parameter

These MUST NOT appear in the YAML parameter list.

## Tool Naming

MCP tool names follow the pattern: `{agent_name}_{command_name}`
Example: `poseidon_shell`, `poseidon_curl`, `poseidon_portscan`
