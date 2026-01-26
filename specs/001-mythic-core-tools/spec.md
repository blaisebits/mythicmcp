# Feature Specification: Mythic Framework Core Tools

**Feature Branch**: `001-mythic-core-tools`
**Created**: 2026-01-25
**Status**: Draft
**Input**: User description: "Mythic framework core tools"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Active Callbacks (Priority: P1)

An operator using an AI assistant wants to see all active callbacks (compromised hosts) in their Mythic operation. They ask the assistant to list callbacks, and the assistant uses the MCP tool to retrieve and display callback information including host details, agent type, and last check-in time.

**Why this priority**: Viewing callbacks is the most fundamental operation in any C2 engagement. Without this, operators cannot see what access they have or make decisions about next steps.

**Independent Test**: Can be fully tested by connecting to a Mythic instance with at least one callback and verifying the tool returns callback data. Delivers immediate visibility into engagement status.

**Acceptance Scenarios**:

1. **Given** a connected Mythic instance with active callbacks, **When** the operator requests callback list, **Then** the system returns all active callbacks with host, user, agent type, and last check-in time
2. **Given** a connected Mythic instance with no callbacks, **When** the operator requests callback list, **Then** the system returns an empty list with a clear message indicating no active callbacks
3. **Given** invalid or expired Mythic credentials, **When** the operator requests callback list, **Then** the system returns a clear authentication error without exposing credentials

---

### User Story 2 - View Operation Details (Priority: P2)

An operator wants to understand the current operation context - its name, operators involved, and high-level statistics. They ask the assistant about the current operation, and it retrieves operation metadata from Mythic.

**Why this priority**: Operation context helps operators confirm they're working in the correct engagement and understand scope. Less critical than callbacks but essential for situational awareness.

**Independent Test**: Can be tested by connecting to a Mythic instance and retrieving operation metadata. Delivers confirmation of operational context.

**Acceptance Scenarios**:

1. **Given** a connected Mythic instance with an active operation, **When** the operator requests operation details, **Then** the system returns operation name, creation date, and operator list
2. **Given** a user with access to multiple operations, **When** the operator requests operation details without specifying which, **Then** the system returns details for the current/default operation

---

### User Story 3 - Check Mythic Server Status (Priority: P3)

An operator wants to verify their connection to the Mythic server is working and check server health before performing operations. They ask the assistant to check the connection, and it confirms connectivity and returns basic server information.

**Why this priority**: Connection verification is a diagnostic tool useful for troubleshooting but not required for core workflows. Operators typically know if they're connected based on other operations succeeding.

**Independent Test**: Can be tested by pointing at both valid and invalid Mythic server addresses. Delivers confidence in server connectivity.

**Acceptance Scenarios**:

1. **Given** valid Mythic server credentials and a reachable server, **When** the operator requests connection status, **Then** the system confirms connectivity and returns server version
2. **Given** unreachable Mythic server, **When** the operator requests connection status, **Then** the system returns a clear connection error with troubleshooting context
3. **Given** reachable server but invalid credentials, **When** the operator requests connection status, **Then** the system distinguishes authentication failure from connectivity failure

---

### User Story 4 - Retrieve Callback Details (Priority: P2)

An operator wants to see detailed information about a specific callback, including its full configuration, integrity level, process information, and recent activity. They specify a callback identifier and the assistant returns comprehensive callback data.

**Why this priority**: After listing callbacks (P1), drilling into specific callback details is the natural next step. Essential for making informed decisions about which callback to use for operations.

**Independent Test**: Can be tested by requesting details for a known callback ID. Delivers deep visibility into a single compromised host.

**Acceptance Scenarios**:

1. **Given** a valid callback ID, **When** the operator requests callback details, **Then** the system returns full callback information including host details, process info, integrity level, and agent configuration
2. **Given** an invalid or non-existent callback ID, **When** the operator requests callback details, **Then** the system returns a clear error indicating the callback was not found
3. **Given** a callback ID from a different operation the user cannot access, **When** the operator requests callback details, **Then** the system returns an authorization error

---

### Edge Cases

- What happens when the Mythic server becomes unreachable mid-operation?
  - System returns a connection error and does not leave operations in an undefined state
- How does the system handle callbacks that go inactive during a query?
  - System returns the last known state with a timestamp indicating when data was retrieved
- What happens when the operator's Mythic session expires?
  - System returns a clear session expiration error and suggests re-authentication
- How are very large callback lists handled (100+ callbacks)?
  - System returns all callbacks; pagination is not required for this scope but results are delivered efficiently

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a tool to list all active callbacks in the current Mythic operation
- **FR-002**: System MUST provide a tool to retrieve detailed information about a specific callback by ID
- **FR-003**: System MUST provide a tool to retrieve current operation metadata (name, operators, creation date)
- **FR-004**: System MUST provide a tool to verify Mythic server connectivity and authentication status
- **FR-005**: System MUST return clear, descriptive errors when Mythic operations fail
- **FR-006**: System MUST NOT expose Mythic credentials in error messages, logs, or tool responses
- **FR-007**: System MUST validate Mythic server reachability before executing any tool operation
- **FR-008**: System MUST include timestamps indicating when data was retrieved from Mythic
- **FR-009**: Each tool MUST have a description clearly stating what Mythic operation it performs

### Key Entities

- **Callback**: A connection from a compromised host to Mythic; key attributes include ID, hostname, username, agent type, integrity level, process ID, last check-in time, and active status
- **Operation**: A Mythic engagement context; key attributes include name, creation date, and associated operators
- **Operator**: A Mythic user with access to operations; key attributes include username and assigned operations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can retrieve callback list within 5 seconds of request for operations with up to 100 callbacks
- **SC-002**: 100% of authentication and connection errors provide actionable troubleshooting information
- **SC-003**: All tool operations complete or fail definitively - no hanging or undefined states
- **SC-004**: Operators can successfully complete the "view callbacks → select callback → view details" workflow without switching tools or interfaces
- **SC-005**: Zero credential exposure in any tool response, error message, or log output

## Assumptions

- Operators have valid Mythic credentials (API token or username/password) configured before using these tools
- The Mythic server is version 3.3 or higher (compatible with the mythic Python library)
- Network connectivity to the Mythic server is generally reliable; tools handle transient failures gracefully
- Operations contain a reasonable number of callbacks (under 1000); extreme scale is out of scope for this feature
- The MCP client (AI assistant) presents tool results to users in a readable format
