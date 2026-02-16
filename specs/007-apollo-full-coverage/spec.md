# Feature Specification: Apollo Full Command Coverage

**Feature Branch**: `007-apollo-full-coverage`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Expand tool coverage for the Apollo agent yaml file to 100% of the apollo commands. Also add a tracking metadata value to the yaml to specify the version of Apollo that the yaml based off"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Apollo Command Access (Priority: P1)

An operator using MythicMCP wants to issue any Apollo command through the MCP interface, not just the 10 currently exposed. Today, commands like `upload`, `cp`, `rm`, `mkdir`, `mv`, `whoami`, `ifconfig`, `kill`, `jobs`, `sleep`, and many others are unavailable, forcing the operator to switch to the Mythic UI for anything beyond basic file ops and shell commands.

**Why this priority**: Without full command coverage, MCP-driven operations hit a wall on routine tasks. This is the core purpose of the feature.

**Independent Test**: Load the updated apollo.yaml, verify all Apollo commands appear as registered MCP tools with correct parameter schemas.

**Acceptance Scenarios**:

1. **Given** the MCP server starts with the updated apollo.yaml, **When** `core_list_plugins` is called, **Then** the Apollo plugin reports a tool count matching the total number of Apollo commands.
2. **Given** any Apollo command exists in the reference agent, **When** the operator looks up the corresponding MCP tool, **Then** the tool exists with correct parameter names, types, and descriptions.
3. **Given** a command with no parameters (e.g., `whoami`, `jobs`), **When** the operator calls it with only `callback_id`, **Then** it executes correctly via `execute_with_validation`.
4. **Given** a command with required parameters (e.g., `cp` with source/destination), **When** the operator omits a required parameter, **Then** validation rejects the call with a clear error.

---

### User Story 2 - Version Tracking Metadata (Priority: P2)

A developer maintaining the Apollo YAML config needs to know which version of the Apollo agent the config was built against. When Apollo releases new commands or changes parameter signatures, the developer must know what version the current YAML targets to identify gaps.

**Why this priority**: Supports maintainability but doesn't block operator functionality.

**Independent Test**: Load apollo.yaml and verify the metadata section contains a version identifier that parses without warnings.

**Acceptance Scenarios**:

1. **Given** the apollo.yaml file, **When** it is parsed by the YAML loader, **Then** a `metadata` section is present containing an `agent_version` field with a version string.
2. **Given** the YAML loader encounters a `metadata` top-level key, **When** parsing, **Then** it does not emit an "unrecognized key" warning.

---

### Edge Cases

- What happens when a command has parameters whose types cannot be expressed in the current YAML schema (e.g., file uploads, arrays, nested objects)? Commands requiring unsupported parameter types are included with the closest supported type (typically `string`) and the description explains the expected format.
- What happens when Apollo adds new commands in a future version? The `agent_version` metadata makes it clear which version was covered, and a developer can diff against the new version.
- What if a command name conflicts with YAML reserved words or Python identifiers? Command names match Mythic's naming which uses lowercase snake_case — no conflicts expected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The apollo.yaml file MUST define tool entries for every Apollo agent command available in the reference implementation, including internal/utility commands (e.g., `load`, `exit`, `sleep`, `blockdlls`).
- **FR-002**: Each tool entry MUST include the correct `name`, `description`, `mythic_command` (if different from name), `timeout`, and `parameters` list matching the reference agent's parameter schema.
- **FR-003**: Parameters MUST use the correct types (`string`, `integer`, `boolean`) and mark `required` status accurately based on the reference implementation.
- **FR-004**: Parameters with default values in the reference MUST carry those defaults in the YAML config.
- **FR-005**: The apollo.yaml MUST include a top-level `metadata` section with an `agent_version` field specifying the Apollo version the config targets.
- **FR-006**: The YAML loader MUST recognize `metadata` as a valid top-level key and not emit warnings when it is present.
- **FR-007**: Commands whose parameters require types not supported by the YAML schema (file uploads, arrays) MUST use `string` type with a description explaining the expected format (e.g., base64-encoded content, comma-separated values).
- **FR-008**: All existing tests MUST continue to pass after the changes.

### Key Entities

- **Command Entry**: A YAML block defining one Apollo command — name, description, mythic_command mapping, timeout, and parameter list.
- **Metadata Section**: A new top-level YAML key (`metadata`) containing version tracking and other config-level information.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Apollo plugin tool count equals the total number of commands in the Apollo reference agent (100% coverage).
- **SC-002**: All tool parameter schemas match the reference agent's parameter definitions (correct types, required flags, defaults).
- **SC-003**: The `metadata.agent_version` field is present and parseable in the loaded config.
- **SC-004**: No "unrecognized key" warnings are emitted for the `metadata` field during YAML loading.
- **SC-005**: All existing unit and integration tests pass without modification (except test assertions on Apollo tool count).

## Clarifications

### Session 2026-02-14

- Q: Should internal/utility commands (builder, load, exit, sleep, spawnto_*, set_injection_technique, blockdlls) be included or excluded? → A: Include all commands — full 1:1 mapping with reference agent.

## Assumptions

- The Apollo reference at `refs/agents/Apollo/` represents the version to target. The `agent_version` will be derived from the reference's version markers (e.g., git tag, version file, or Mythic compatibility version).
- Commands that require Mythic-specific parameter types (file browser, payload selection) will use `string` parameters with descriptive text explaining the expected input format.
- The `metadata` top-level key will be handled by adding it as an explicit optional field on `YamlConfigModel` so it doesn't trigger the unrecognized-key warning.
- Command timeout defaults will use 60s for quick commands, 120s for file transfer / assembly execution commands, and 300s for long-running operations, consistent with existing patterns.
