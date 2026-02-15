# Feature Specification: YAML-Driven Agent Plugin Configuration

**Feature Branch**: `006-yaml-plugin-config`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "Overhaul the agent plugin system to use a yaml configuration to define the commands available. Start with Apollo as the first test case."

## User Scenarios & Testing

### User Story 1 - Define Agent Commands via Configuration File (Priority: P1)

An operator wants to add or modify the commands available for an agent without writing or editing handler code. They create or edit a configuration file that declares the agent's metadata (name, description, supported platforms) and the list of commands it supports, including each command's parameters, types, defaults, and constraints. When the server starts, it reads this configuration and automatically registers the corresponding tools.

**Why this priority**: This is the core value proposition of the feature. Without configuration-driven command definitions, every change requires modifying code. This story delivers the fundamental capability.

**Independent Test**: Can be fully tested by creating a configuration file for Apollo, starting the server, and verifying that all 10 Apollo tools appear and are callable with correct parameter schemas.

**Acceptance Scenarios**:

1. **Given** a valid agent configuration file exists for Apollo with all 10 commands defined, **When** the server starts, **Then** all 10 tools are registered with correct names (e.g., `apollo_shell`), descriptions, and parameter schemas.
2. **Given** a command definition includes parameter constraints (minimum, maximum, default values), **When** the tool is called with an out-of-range value, **Then** the system rejects the input with a validation error before execution.
3. **Given** a command definition includes a parameter with a default value, **When** the tool is called without that parameter, **Then** the default value is used.

---

### User Story 2 - Maintain Backward Compatibility with Existing Tool Behavior (Priority: P1)

An operator currently using Apollo tools (shell, pwd, ls, cd, cat, ps, run, download, execute_assembly, screenshot) expects the exact same tool names, parameter names, descriptions, and execution behavior after the migration. The configuration-driven approach must produce tools that are indistinguishable from the current hard-coded implementations.

**Why this priority**: Breaking existing workflows would block adoption. This story ensures the overhaul is transparent to users.

**Independent Test**: Can be tested by running the existing integration test suite against the configuration-driven Apollo plugin and verifying identical results.

**Acceptance Scenarios**:

1. **Given** the Apollo plugin is migrated to configuration-driven definition, **When** an operator lists available tools, **Then** the same 10 tools appear with identical names and descriptions as the current implementation.
2. **Given** the Apollo plugin is configuration-driven, **When** an operator calls `apollo_shell` with a callback ID and command, **Then** the command executes on the target and returns output in the same response format.
3. **Given** the Apollo plugin is configuration-driven, **When** an operator calls any Apollo tool with invalid parameters, **Then** the same validation errors are returned as the current implementation.

---

### User Story 3 - Validate Configuration Files at Startup (Priority: P2)

An operator edits a configuration file and introduces an error (missing required field, invalid parameter type, duplicate command name). When the server starts, it detects the error, reports a clear message identifying the file and the specific problem, and skips the invalid plugin while continuing to load valid ones.

**Why this priority**: Without validation, configuration errors would cause cryptic runtime failures. Early detection with clear messages is essential for usability.

**Independent Test**: Can be tested by creating deliberately invalid configuration files and verifying the server produces specific, actionable error messages.

**Acceptance Scenarios**:

1. **Given** a configuration file is missing the agent name field, **When** the server starts, **Then** it reports an error identifying the file and the missing field, and skips loading that plugin.
2. **Given** a configuration file defines a command with an unsupported parameter type, **When** the server starts, **Then** it reports an error identifying the command and the invalid type.
3. **Given** a configuration file defines two commands with the same name, **When** the server starts, **Then** it reports an error about the duplicate and skips the plugin.
4. **Given** a configuration file has valid structure but an unrecognized top-level field, **When** the server starts, **Then** it reports a warning about the unrecognized field but loads the plugin successfully.

---

### User Story 4 - Add a New Agent Plugin Without Writing Code (Priority: P2)

An operator wants to support a new Mythic agent (e.g., a custom agent) by creating only a configuration file. They define the agent metadata and commands in the configuration format, place the file in the appropriate directory, and restart the server. The new agent's tools become available immediately.

**Why this priority**: This is the long-term payoff of the configuration approach -- removing the code requirement for new agents.

**Independent Test**: Can be tested by creating a minimal configuration file for a fictitious agent with one command, starting the server, and verifying the tool appears in the tool list.

**Acceptance Scenarios**:

1. **Given** a new configuration file is placed in the plugins directory for agent "testagent" with a single "ping" command, **When** the server starts, **Then** `testagent_ping` appears in the tool list with correct metadata.
2. **Given** the new agent's configuration defines supported platforms as Linux only, **When** an operator queries plugin info, **Then** the plugin reports Linux as its supported platform.

---

### Edge Cases

- What happens when a configuration file references a command name that doesn't exist in the Mythic agent? The system registers the tool; execution will fail at the Mythic API level with an appropriate error returned to the operator.
- What happens when two configuration files define the same agent name? The system reports an error identifying both files and the conflicting agent name, and skips loading both plugins.
- What happens when a configuration file defines zero commands? The system rejects the configuration with an error identifying the file and the missing commands, and skips loading that plugin.
- What happens when the configuration directory does not exist? The system logs an informational message and continues with no plugins loaded.
- What happens when a parameter name in the configuration conflicts with a reserved name (e.g., "ctx", "context", "self")? The system rejects the configuration with a clear error message identifying the reserved name and the command it appears in.

## Requirements

### Functional Requirements

- **FR-001**: System MUST support defining agent plugins entirely through structured configuration files without requiring handler code.
- **FR-002**: System MUST read configuration files from the builtin plugins directory and an optional external plugins directory. Each configuration file defines exactly one agent (one file per agent, e.g., `apollo.yaml`).
- **FR-003**: Each configuration file MUST define agent metadata: name, description, and supported operating systems.
- **FR-004**: Each configuration file MUST define one or more commands, where each command includes a name, description, the Mythic command name to execute, and its parameters.
- **FR-005**: Command parameters MUST support type declarations (string, integer, boolean), required/optional status, default values, validation constraints (minimum, maximum, allowed values), and a role designation of either "task" (sent to Mythic) or "meta" (consumed locally by the executor). The parameters `callback_id` and `timeout` default to "meta"; all others default to "task".
- **FR-006**: System MUST auto-generate tool handlers from configuration that use the existing execution pipeline (agent type validation, task issuance, output collection).
- **FR-007**: System MUST validate all configuration files at startup and report specific, actionable errors for any invalid configurations.
- **FR-008**: System MUST namespace tool names as `{agent_name}_{command_name}` to prevent collisions across agents.
- **FR-009**: System MUST preserve the existing plugin registry interface so that `core_list_plugins` and other introspection tools continue to work.
- **FR-010**: The Apollo agent MUST be fully migrated from code-defined tools to configuration-defined tools as the reference implementation. The previous code-based Apollo plugin file MUST be deleted after migration; the YAML configuration becomes the sole definition.
- **FR-011**: System MUST support a default timeout per command, overridable by the operator at call time via a timeout parameter.
- **FR-012**: System MUST continue to support code-based plugins alongside configuration-based plugins for advanced use cases requiring custom handler logic.

### Key Entities

- **Agent Configuration**: Defines an agent's identity (name, description, platforms) and its available commands. One configuration per agent.
- **Command Definition**: A single command within an agent, specifying the Mythic command to execute, its user-facing description, and parameter schema.
- **Parameter Definition**: A single parameter for a command, specifying name, type, constraints, default value, and description.
- **Plugin Registry**: Central catalog of all loaded plugins (both configuration-based and code-based), providing tool lookup and introspection.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 10 Apollo tools are fully operational when defined through configuration, with identical behavior to the current code-based implementation.
- **SC-002**: A new agent plugin with 3 commands can be created by writing only a configuration file, with zero lines of handler code.
- **SC-003**: Configuration validation catches 100% of structural errors (missing fields, invalid types, duplicates) at startup with messages that identify the file and specific problem.
- **SC-004**: The total lines of plugin definition code decreases by at least 30% after migrating Apollo to configuration-driven definitions.
- **SC-005**: Existing integration tests pass without modification after the Apollo migration.

## Clarifications

### Session 2026-02-15

- Q: How should config parameters map to Mythic task parameters vs local executor parameters? → A: Config distinguishes "task" vs "meta" parameters; `callback_id`/`timeout` default to meta.
- Q: What happens to the code-based `apollo.py` after migration to YAML config? → A: Delete it entirely; YAML config is the sole Apollo definition. Arachne remains code-based to validate FR-012.
- Q: One config file per agent or multi-agent config files? → A: One YAML file per agent (e.g., `apollo.yaml`). Keeps files small, independently validatable, and simplifies error reporting.

## Assumptions

- The configuration file format will use YAML, which is already a project dependency (used in integration test config).
- All configuration-driven commands follow the same execution pattern: validate agent type, issue task, collect output. Commands requiring custom logic (e.g., file encoding, multi-step workflows) will remain as code-based plugins.
- The `kwargs` parameter pattern currently used in the MCP tool interface will be preserved -- configuration-driven tools will serialize their parameters into the kwargs string format expected by the existing executor.
- External plugin authors can create configuration files in the same format and place them in the external plugins directory.
- The Arachne migration to configuration-driven definitions is a follow-on effort, not part of this feature's scope. However, the system must be designed to support it.
