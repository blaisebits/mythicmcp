# Data Model: Poseidon Agent Built-in Plugin

## Entities

### PoseidonPluginConfig (poseidon.yaml)

The YAML file parsed by the existing `YamlConfigModel` Pydantic validator.

| Field | Type | Description |
|-------|------|-------------|
| agent.name | string | "poseidon" |
| agent.description | string | Agent description |
| agent.supported_os | list[string] | ["macOS", "Linux"] |
| metadata.agent_version | string | "2.2.8" |
| metadata.mythic_version | string | "3.3.0+" |
| commands | list[CommandConfig] | ~76 command definitions |

### CommandConfig

Each command entry in the YAML `commands` list.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | MCP tool suffix (e.g., "shell" → `poseidon_shell`) |
| description | string | yes | Tool description shown to MCP clients |
| mythic_command | string | no | Mythic command name (defaults to `name`) |
| timeout | integer | no | Default timeout 30-300s (default: 60) |
| parameters | list[ParameterConfig] | no | Command parameters |

### ParameterConfig

Each parameter entry within a command.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Parameter name (valid Python identifier) |
| type | string | yes | "string", "integer", or "boolean" |
| description | string | yes | Parameter description |
| required | boolean | no | Default: true |
| default | any | no | Default value (sets required=false) |
| choices | list[string] | no | Valid choices (string type only) |
| min | integer | no | Minimum value (integer type only) |
| max | integer | no | Maximum value (integer type only) |

## Relationships

```
poseidon.yaml
  └── agent (1) ──→ AgentConfigModel
  └── commands (N) ──→ CommandConfigModel
       └── parameters (M) ──→ ParameterConfigModel
```

At startup: `poseidon.yaml` → `parse_yaml_config()` → `YamlConfigModel` → `YamlAgentPlugin` → N × `ToolDefinition` registered with MCP server.

## No State Transitions

Plugin is stateless. YAML is parsed once at startup. No runtime state changes.
