# Feature Specification: Core Payload Tools

**Feature Branch**: `010-core-payload-tools`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Adding new core tools around handling payloads"

## Clarifications

### Session 2026-03-15

- Q: Should wrapper payload creation (payloads that embed another payload) be in scope? → A: Out of scope — exclude and document as future work.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List All Payloads (Priority: P1)

An operator wants to see all payloads that exist in their current Mythic operation to understand what agents have been built, their build status, and which payload types and C2 profiles are in use.

**Why this priority**: Visibility into existing payloads is foundational — operators need to know what's already built before creating new ones or troubleshooting callbacks.

**Independent Test**: Can be fully tested by listing payloads in an operation that has at least one payload built and verifying the returned metadata matches Mythic UI.

**Acceptance Scenarios**:

1. **Given** an active operation with payloads, **When** the operator lists payloads, **Then** they receive a summary of each payload including its UUID, agent type, build status, OS, description, and associated C2 profiles.
2. **Given** an active operation with no payloads, **When** the operator lists payloads, **Then** they receive an empty list with a count of zero.
3. **Given** no current operation is set, **When** the operator lists payloads, **Then** they receive a clear error indicating they must set an operation first.

---

### User Story 2 - Get Payload Details (Priority: P1)

An operator wants to retrieve detailed information about a specific payload by its UUID — including build messages, C2 profile configuration, and file metadata.

**Why this priority**: Inspecting individual payloads is essential for debugging build failures, verifying configuration before deployment, and understanding callback behavior.

**Independent Test**: Can be tested by requesting details for a known payload UUID and verifying returned fields match the Mythic UI payload details page.

**Acceptance Scenarios**:

1. **Given** a valid payload UUID, **When** the operator requests payload details, **Then** they receive complete payload information including build phase, agent type, OS, C2 profiles, description, creation time, operator, and file metadata.
2. **Given** an invalid or nonexistent payload UUID, **When** the operator requests payload details, **Then** they receive a clear error indicating the payload was not found.

---

### User Story 3 - Create a Payload (Priority: P2)

An operator wants to build a new standard payload by specifying the agent type, target OS, C2 profile configuration, and optionally which commands to include and build parameters. The system tasks Mythic to build the payload and returns the result. Wrapper payloads (payloads that embed another payload) are out of scope for this feature.

**Why this priority**: Creating payloads programmatically enables automation workflows and removes the need to switch to the Mythic UI for payload generation.

**Independent Test**: Can be tested by creating a payload with valid parameters and verifying it reaches a terminal build state (success or error) with appropriate build output.

**Acceptance Scenarios**:

1. **Given** valid payload parameters (agent type, OS, C2 profile with parameters), **When** the operator creates a payload, **Then** Mythic builds the payload and returns the build result including UUID, build status, and any build messages.
2. **Given** a request to include all commands, **When** the operator creates a payload with the include-all-commands option, **Then** all available commands for that agent type are included.
3. **Given** invalid parameters (e.g., nonexistent agent type), **When** the operator creates a payload, **Then** they receive a clear error from Mythic describing what went wrong.
4. **Given** a payload build that takes too long, **When** the timeout is exceeded, **Then** the operator receives a timeout error with the payload UUID so they can check status later.

---

### User Story 4 - Download a Payload (Priority: P2)

An operator wants to download the compiled payload binary by its UUID so they can deploy it to a target or inspect its contents.

**Why this priority**: Downloading the built artifact is a natural follow-up to creating or listing payloads, completing the payload lifecycle.

**Independent Test**: Can be tested by downloading a successfully built payload and verifying the returned content is non-empty and the metadata (filename, UUID) is correct.

**Acceptance Scenarios**:

1. **Given** a successfully built payload UUID, **When** the operator downloads the payload, **Then** they receive the payload binary as base64-encoded content along with filename and size metadata.
2. **Given** a payload UUID that failed to build, **When** the operator downloads it, **Then** they receive an error indicating the payload is not available for download.
3. **Given** an invalid UUID, **When** the operator tries to download, **Then** they receive a not-found error.

---

### User Story 5 - Check Payload Configuration (Priority: P3)

An operator wants to validate a payload's C2 configuration against the running C2 profile to confirm the payload will be able to communicate properly once deployed.

**Why this priority**: Configuration validation catches mismatches before deployment, saving time and avoiding failed callbacks.

**Independent Test**: Can be tested by running a config check on a payload with a known-good C2 configuration and verifying the result.

**Acceptance Scenarios**:

1. **Given** a payload with valid C2 configuration, **When** the operator checks the config, **Then** they receive a success status with any relevant output.
2. **Given** a payload with misconfigured C2 parameters, **When** the operator checks the config, **Then** they receive an error status describing the mismatch.
3. **Given** no current operation is set, **When** the operator checks the config, **Then** they receive a clear error indicating they must set an operation first.

---

### User Story 6 - Get Payload Redirect Rules (Priority: P3)

An operator wants to retrieve the redirect rules for a payload so they can configure redirectors or verify traffic routing.

**Why this priority**: Redirect rules are needed for operational infrastructure setup but are not required for basic payload workflows.

**Independent Test**: Can be tested by requesting redirect rules for a payload and verifying the response contains rule data.

**Acceptance Scenarios**:

1. **Given** a valid payload UUID, **When** the operator requests redirect rules, **Then** they receive the rules output for that payload's C2 configuration.
2. **Given** an invalid UUID, **When** the operator requests redirect rules, **Then** they receive a not-found error.
3. **Given** no current operation is set, **When** the operator requests redirect rules, **Then** they receive a clear error indicating they must set an operation first.

---

### Edge Cases

- If the Mythic server connection is lost or times out mid-payload-build, the tool returns a timeout error including the payload UUID so the operator can check build status later via `core_get_payload`.
- List payloads returns all payloads (including auto-generated and deleted) with metadata flags so consumers can filter as needed.
- Large payload lists (hundreds of payloads) are returned in full — no pagination; Mythic returns all results in a single query.
- Create payload proceeds regardless of whether the C2 profile is currently running; operators can use `core_check_payload_config` afterward to validate.
- Wrapper payload creation is out of scope for this feature (future work).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST list all payloads in the current operation, returning UUID, agent type, build status, OS, description, C2 profile names, creation time, and whether the payload was auto-generated or deleted.
- **FR-002**: System MUST retrieve detailed payload information by UUID, including build phase, build messages (stdout/stderr), operator, file metadata (file UUID, filename), and C2 profile details (name, running status, P2P status).
- **FR-003**: System MUST create a new standard payload (not wrapper payloads) given agent type name, filename, target OS, and C2 profile configuration (profile name + parameter key/value pairs).
- **FR-004**: System MUST support optional parameters for payload creation: command list, build parameters, description, and an include-all-commands flag.
- **FR-005**: System MUST wait for payload build completion by default and return the final build result, with a configurable timeout.
- **FR-006**: System MUST download a built payload's binary content by UUID, returning it as base64-encoded data with filename and size metadata.
- **FR-007**: System MUST validate a payload's C2 configuration against the running C2 profile and return the check result (status, error, output).
- **FR-008**: System MUST retrieve redirect rules for a payload by UUID and return the rules (status, error, output).
- **FR-009**: System MUST return clear, typed errors for common failure cases: no operation set, payload not found, build failure, connection error, timeout.
- **FR-010**: All responses MUST include a UTC timestamp indicating when the data was retrieved, consistent with existing core tool patterns.

### Out of Scope

- Wrapper payload creation (payloads that embed another payload) — future feature.
- Payload deletion or removal.

### Key Entities

- **Payload**: A built agent binary — identified by UUID, associated with an agent type, target OS, C2 profiles, build status, and optionally a downloadable file.
- **C2 Profile Configuration**: A C2 communication profile (e.g., HTTP, SMB) with its parameter key/value pairs, used when creating a payload.
- **Build Parameters**: Agent-specific build options (key/value pairs) that control compilation behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can list all payloads in an operation and identify each payload's agent type, build status, and C2 profile in a single tool call.
- **SC-002**: Operators can inspect any payload's full configuration and build output without switching to the Mythic web UI.
- **SC-003**: Operators can create a new payload and receive the build result (success or failure with diagnostics) in a single tool call.
- **SC-004**: Operators can download a built payload binary for deployment without leaving the MCP client.
- **SC-005**: Operators can validate payload C2 configuration before deployment, catching mismatches proactively.
- **SC-006**: All six payload tools follow the same response patterns (typed models, UTC timestamps, error categories) as existing core tools, requiring no new learning for operators already using MythicMCP.
