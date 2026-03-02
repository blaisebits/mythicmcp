# Feature Specification: Poseidon Agent Built-in Plugin

**Feature Branch**: `008-poseidon-plugin`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Poseidon agent built-in plugin support"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Commands on macOS/Linux Targets via Poseidon (Priority: P1)

An operator with an active Poseidon callback wants to run commands through the MCP server. They issue Poseidon-specific tools (shell, run, curl, ls, cat, etc.) against a callback ID and receive command output.

**Why this priority**: Core value — without command execution, the plugin has no purpose.

**Independent Test**: Operator can issue `poseidon_shell` with a callback_id and command string, and receive output from the target system.

**Acceptance Scenarios**:

1. **Given** an active Poseidon callback, **When** the operator calls `poseidon_shell` with a command, **Then** the command executes on the target and output is returned.
2. **Given** an active Poseidon callback, **When** the operator calls `poseidon_ls` with a path, **Then** directory contents are returned.
3. **Given** no active Poseidon callback for the given ID, **When** the operator calls any Poseidon tool, **Then** a clear error is returned indicating the callback is invalid or inactive.

---

### User Story 2 - Full Poseidon Command Coverage (Priority: P1)

An operator needs access to the complete Poseidon 2.2.8 command set — shell execution, file operations, process management, network recon, credential operations, persistence, code injection, system info, XPC (macOS), and agent configuration — all exposed as individual MCP tools.

**Why this priority**: Partial coverage forces operators to fall back to the Mythic UI, defeating the purpose of MCP integration.

**Independent Test**: All Poseidon commands listed in the agent's command set are available as MCP tools after plugin load. Each tool validates its parameters and delegates to the correct Mythic command.

**Acceptance Scenarios**:

1. **Given** the Poseidon plugin is loaded, **When** the operator calls `core_list_plugins`, **Then** Poseidon appears with the correct tool count and supported OS list (macOS, Linux).
2. **Given** the plugin is loaded, **When** the operator lists available tools, **Then** every Poseidon command has a corresponding `poseidon_<command>` tool.
3. **Given** a tool with required parameters, **When** the operator omits a required parameter, **Then** a validation error is returned before any task is issued.

---

### User Story 3 - Plugin Loads Automatically at Startup (Priority: P2)

When the MCP server starts, the Poseidon YAML plugin is discovered and loaded from the built-in plugins directory alongside Apollo and Arachne, with no manual configuration required.

**Why this priority**: Seamless startup experience — operators shouldn't need to configure built-in plugins.

**Independent Test**: Start the MCP server and verify `core_list_plugins` includes Poseidon with correct metadata.

**Acceptance Scenarios**:

1. **Given** a fresh MCP server startup, **When** plugins are loaded, **Then** the Poseidon plugin loads without errors.
2. **Given** the Poseidon plugin is loaded, **When** queried, **Then** it reports agent name "poseidon", supported OS ["macOS", "Linux"], and the correct number of tools.

---

### User Story 4 - Integration Tests Cover Poseidon Commands (Priority: P3)

The integration test config sample includes Poseidon-specific test commands so operators with a Poseidon callback can validate the plugin end-to-end.

**Why this priority**: Test coverage ensures reliability but isn't blocking for initial use.

**Independent Test**: Add Poseidon entries to `config.sample.yaml` with representative commands (shell, ls, pwd, cat, ps, ifconfig, upload, download).

**Acceptance Scenarios**:

1. **Given** the sample config includes Poseidon test commands, **When** an operator configures a Poseidon target, **Then** the integration test suite exercises Poseidon tools.

---

### Edge Cases

- What happens when a macOS-only command (jxa, libinject, persist_launchd) is issued against a Linux callback? The Mythic server rejects it; the MCP tool should surface the error clearly.
- What happens when the Poseidon plugin YAML has a syntax error? The YAML loader should report a startup validation error and skip the plugin without crashing.
- What happens when commands with parameter groups (upload with "New File" vs "Existing File") are called? The YAML plugin should accept the flat parameter set and let Mythic handle group routing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a YAML plugin definition (`poseidon.yaml`) in the built-in plugins directory that covers all Poseidon 2.2.8 commands.
- **FR-002**: Each Poseidon command MUST be exposed as a `poseidon_<command>` MCP tool with appropriate parameter definitions (name, type, description, required/optional, defaults).
- **FR-003**: The plugin MUST declare supported operating systems as macOS and Linux.
- **FR-004**: Commands with platform restrictions (macOS-only) MUST have their tool name suffixed with `_macos` (e.g., `poseidon_jxa_macos`) and include "(macOS only)" in their tool description.
- **FR-005**: The plugin MUST load automatically at server startup via the existing YAML loader with no code changes to the loader itself.
- **FR-006**: Parameters using Mythic FILE type (file_id references) MUST be typed as string with descriptions indicating the file_id comes from `core_upload_file`.
- **FR-007**: Commands accepting array parameters (portscan hosts/ports, curl headers) MUST document the expected format in the parameter description.
- **FR-008**: The unit test suite MUST include tests verifying the Poseidon YAML loads correctly and produces the expected number of tools.
- **FR-009**: The integration test sample config MUST include a Poseidon section with representative test commands.
- **FR-010**: Commands with choose-one semantics (curl method, etc.) MUST use the `choices` field on string parameters.

### Key Entities

- **Poseidon Plugin Config**: YAML file defining agent metadata and all commands with parameters. Follows the same schema as Apollo and Arachne YAML configs.
- **Poseidon Command**: A single agent command (e.g., `shell`, `curl`, `portscan`) mapped to an MCP tool with validated parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Poseidon 2.2.8 commands are available as MCP tools after plugin load (target: 70+ tools).
- **SC-002**: The YAML plugin loads at startup without errors and appears in `core_list_plugins` output.
- **SC-003**: All existing unit tests continue to pass after adding the Poseidon plugin.
- **SC-004**: The Poseidon plugin follows the same YAML structure and conventions as the Apollo plugin, requiring no changes to the YAML loader.
- **SC-005**: An operator can issue any Poseidon command via MCP tools and receive the same result as issuing it through the Mythic UI.

## Assumptions

- Poseidon version targeted is 2.2.8 (matching the reference agent in `/refs/agents/poseidon/`).
- The existing YAML plugin loader supports all parameter types needed by Poseidon (string, integer, boolean). Array and choose-one parameters are handled via string type with descriptive documentation and the `choices` field respectively.
- macOS-only command restrictions are documented in tool descriptions but not enforced at the MCP layer — Mythic server handles OS validation.
- Parameter groups (e.g., upload's "New File" vs "Existing File") are flattened to optional parameters in the YAML definition, matching the Apollo plugin pattern.
