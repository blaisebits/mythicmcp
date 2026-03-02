# Feature Specification: Arachne Full Command Coverage

**Feature Branch**: `009-arachne-full-coverage`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "Expand cover for Arachne to cover all commands"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Broken Upload and Execute Assembly Commands (Priority: P1)

An operator attempts to upload a file to a target via an Arachne webshell or execute a .NET assembly. Currently these commands have parameter mismatches between the YAML config and Mythic's actual API, causing failures.

**Why this priority**: Upload and execute_assembly are critical offensive capabilities. Parameter type/name mismatches in the current YAML config make them non-functional.

**Independent Test**: Task an Arachne callback with `arachne_upload` providing a file and remote path, and with `arachne_execute_assembly` providing an assembly file and arguments. Both should execute successfully.

**Acceptance Scenarios**:

1. **Given** an active Arachne callback, **When** operator uses `arachne_upload` with a file and remote path, **Then** the file is written to the target at the specified path
2. **Given** an active Arachne ASPX callback on Windows, **When** operator uses `arachne_execute_assembly` with a .NET assembly file and arguments, **Then** the assembly executes and output is returned

---

### User Story 2 - Fix Download Parameter Name Mismatch (Priority: P1)

An operator uses `arachne_download` to retrieve a file from a target. The YAML config uses parameter name `path` but Mythic expects `file_path`, causing command failure.

**Why this priority**: Download is a core file operations capability that is currently broken.

**Independent Test**: Task an Arachne callback with `arachne_download` specifying a file path. The file should be retrieved from the target.

**Acceptance Scenarios**:

1. **Given** an active Arachne callback and a known file on the target, **When** operator uses `arachne_download` with the file path, **Then** the file is downloaded to Mythic
2. **Given** an active Arachne callback, **When** operator specifies a non-existent file path, **Then** an appropriate error message is returned

---

### User Story 3 - Correct Platform Restrictions (Priority: P2)

The `cd` and `execute_assembly` commands are marked as supporting both Windows and Linux, but the Arachne agent restricts `cd` to Windows-only and `execute_assembly` to Windows/ASPX-only. Operators get confusing errors on unsupported platforms.

**Why this priority**: Incorrect platform metadata misleads operators. Less urgent than broken parameters but affects usability.

**Independent Test**: Verify command descriptions and platform annotations accurately reflect Windows-only restrictions for `cd` and `execute_assembly`.

**Acceptance Scenarios**:

1. **Given** the Arachne plugin YAML, **When** examining `cd` command metadata, **Then** it indicates Windows-only support
2. **Given** the Arachne plugin YAML, **When** examining `execute_assembly` command metadata, **Then** it indicates Windows/ASPX-only support

---

### User Story 4 - Add Agent Version Metadata (Priority: P3)

Following the pattern from Apollo full coverage (007), the Arachne YAML should include metadata with the agent version for traceability.

**Why this priority**: Improves maintainability. Low priority since it doesn't affect functionality.

**Independent Test**: Verify the YAML includes a metadata section with agent version.

**Acceptance Scenarios**:

1. **Given** the Arachne plugin YAML, **When** loaded by the plugin system, **Then** agent version metadata is present

---

### Edge Cases

- What happens when `upload` is called with a file exceeding webshell size limits?
- How does `execute_assembly` behave on a non-ASPX (PHP/JSP) Arachne callback?
- What happens when `cd` is tasked on a Linux Arachne callback?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `download` command MUST use the correct Mythic parameter name (`file_path`) so the task executes successfully
- **FR-002**: The `upload` command MUST accept a Mythic file reference (file_id) instead of base64-encoded string content, matching Mythic's File parameter type
- **FR-003**: The `execute_assembly` command MUST accept a Mythic file reference (file_id) and arguments string, matching Mythic's actual parameter schema (`file` + `arguments`)
- **FR-004**: The `cd` command MUST be annotated as Windows-only to match the agent's actual platform support
- **FR-005**: The `execute_assembly` command MUST be annotated as Windows/ASPX-only to match the agent's actual platform support
- **FR-006**: The Arachne YAML MUST include metadata with the target agent version (0.0.4)
- **FR-007**: All 8 user-taskable Arachne commands (shell, pwd, ls, cd, rm, download, upload, execute_assembly) MUST have parameter names, types, and defaults matching the Mythic agent source

### Assumptions

- The `checkin` command is intentionally excluded — it is an internal/automatic command for initial system info gathering, not operator-taskable
- Target Arachne agent version is 0.0.4 per the reference implementation
- The YAML plugin loader already supports `file` type parameters based on Apollo's implementation (e.g., `powershell_import`, `upload`, `register_assembly`)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 8 Arachne MCP tools pass parameter validation when called with correct inputs
- **SC-002**: Upload and execute_assembly commands successfully execute against a live Arachne callback
- **SC-003**: Download command successfully retrieves files from a target via Arachne callback
- **SC-004**: No parameter name or type mismatches exist between the Arachne YAML config and the Mythic agent's actual command definitions
