# Research: YAML-Driven Agent Plugin Configuration

**Feature**: 006-yaml-plugin-config
**Date**: 2026-02-15

## R1: YAML Configuration Schema Design

**Decision**: Use a flat YAML schema with `agent` top-level key containing metadata and a `commands` list. Each command has `name`, `description`, `mythic_command`, `timeout`, and a `parameters` list.

**Rationale**: Matches the existing data model (AgentPlugin → ToolDefinition → Pydantic params). The `mythic_command` field allows the config command name to differ from the Mythic-side command name if needed (though they'll typically match). Flat structure avoids unnecessary nesting depth.

**Alternatives considered**:
- Nested agent-per-key structure (e.g., `apollo: commands: ...`) — rejected because spec requires one file per agent, making the agent name as a key redundant.
- JSON Schema for validation — rejected as over-engineering; Pydantic models provide validation at load time.

## R2: Parameter Type System

**Decision**: Support 3 types: `string`, `integer`, `boolean`. Map directly to Python `str`, `int`, `bool`. Constraints: `min`/`max` for integers, `choices` for strings, `default` for all types.

**Rationale**: These 3 types cover 100% of current Apollo and Arachne parameter definitions. No current parameter uses float, list, or complex types. Adding more types later is straightforward.

**Alternatives considered**:
- Full JSON Schema type system — rejected as over-engineering for current needs.
- Supporting `float` and `list` — deferred until an agent actually needs them.

## R3: Parameter Role Designation (task vs meta)

**Decision**: Parameters have a `role` field defaulting to `"task"`. The reserved parameters `callback_id` and `timeout` auto-default to `"meta"` role. Task-role parameters are collected into the `parameters` dict passed to `execute_with_validation()`. Meta-role parameters are consumed by the executor framework.

**Rationale**: Per clarification session. Explicit but not verbose. The auto-default for `callback_id`/`timeout` means most configs won't need to specify role at all.

**Alternatives considered**:
- Implicit convention only (no role field) — rejected for lack of extensibility.
- Separate `meta_parameters` and `task_parameters` lists — rejected for verbosity.

## R4: Handler Auto-Generation Strategy

**Decision**: Generate handler functions at plugin load time that extract task-role parameters from the Pydantic model instance, build the parameters dict, and call `execute_with_validation()`. The generated handler is functionally equivalent to the current hand-written Apollo handlers.

**Rationale**: All 10 Apollo handlers and all 8 Arachne handlers follow the exact same pattern: extract params → call `execute_with_validation(ctx, callback_id, agent_type, command_name, {param_dict}, timeout)`. This pattern is 100% mechanical and can be generated from config.

**Alternatives considered**:
- Template-based code generation (generate .py files) — rejected; runtime generation is simpler and avoids generated code maintenance.
- Using a generic handler class — equivalent complexity, less idiomatic.

## R5: YAML Library Choice

**Decision**: Use PyYAML (`pyyaml>=6.0.0`), which is already a dev dependency. Move it to main dependencies.

**Rationale**: Already in the project's dependency graph. Well-established, standard library for YAML in Python. `yaml.safe_load()` provides safe deserialization.

**Alternatives considered**:
- `ruamel.yaml` — more features but unnecessary for read-only config loading.
- `tomllib` (stdlib) — TOML is less readable for deeply nested structures like parameter definitions.

## R6: Config File Discovery

**Decision**: Discover `.yaml` and `.yml` files in the builtin plugins directory and external plugins directory. Skip files starting with `_` or `.`. Process alongside existing `.py` discovery.

**Rationale**: Consistent with existing plugin discovery patterns. Supporting both extensions is standard practice.

**Alternatives considered**:
- Only `.yaml` extension — unnecessarily restrictive.
- Subdirectory-per-agent — over-engineering for a single file per agent.

## R7: Coexistence with Code-Based Plugins

**Decision**: The plugin loader processes YAML configs first, then Python modules. If a YAML config and a Python module define the same agent name, the loader reports a conflict and loads only the YAML version (config takes precedence).

**Rationale**: During migration, this ensures the YAML config is authoritative when both exist. After Apollo migration, `apollo.py` is deleted so no conflict arises. Arachne remains `.py` only.

**Alternatives considered**:
- Python takes precedence — confusing when explicitly migrating to YAML.
- Error on conflict — too strict during incremental migration.

## R8: Validation Model

**Decision**: Use Pydantic models to validate the parsed YAML structure. Define `AgentConfigModel`, `CommandConfigModel`, and `ParameterConfigModel` that validate the config at load time. Validation errors are collected and reported per-file with file path and specific field.

**Rationale**: Pydantic is already a project dependency and provides excellent error messages. Using it for config validation keeps the approach consistent with the rest of the codebase.

**Alternatives considered**:
- Manual validation with if/else — error-prone, verbose.
- JSON Schema validation — adds a dependency and is less Pythonic.
