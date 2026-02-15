# Feature Specification: Integration Testing Pipeline

**Feature Branch**: `005-integration-testing`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Adding additional integration testing for generating payloads, downloading payloads, uploading them to target systems for execution, verifying callbacks, and executing test commands. These systems should be configured from a yaml file in the repository."

## Clarifications

### Session 2026-02-08

- Q: Should the test pipeline clean up generated payloads and callbacks after completion? → A: Full cleanup — remove uploaded payloads from targets and exit new callbacks after test completion.
- Q: What are the target test systems? → A: Two systems — one running Debian Linux and one running Windows 11.
- Q: How should agent types map to target systems? → A: Explicit mapping — each target system in YAML lists which agent types to test on it.
- Q: Should the pipeline be one end-to-end test or separate tests per phase? → A: Separate tests per phase with dependencies — later phases skip if earlier phases fail for the same agent/target.
- Q: Should the YAML config include Mythic server connection or reuse existing env vars? → A: YAML contains everything including Mythic connection — fully self-contained config file.
- Q: What should be committed to the repo as a config reference? → A: Sample file with placeholders — commit `config.sample.yaml` with dummy values and comments.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - YAML-Configured Test Environment (Priority: P1)

An operator defines their test environment in a YAML configuration file stored in the repository. This file describes the Mythic server connection, available target systems (hostnames, access method, OS type), agent types to test, and test commands to run. The testing framework reads this configuration and uses it to drive all integration tests, so that tests are reproducible and environment-specific details are not hardcoded.

**Why this priority**: Without configuration, no other test scenarios can execute. This is the foundation that all other stories depend on.

**Independent Test**: Can be fully tested by loading and validating a sample YAML configuration file and confirming all required fields are parsed correctly and invalid configurations are rejected with clear error messages.

**Acceptance Scenarios**:

1. **Given** a valid YAML configuration file exists in the repository, **When** the test framework starts, **Then** it loads all target system definitions, Mythic connection details, agent configurations, and test commands successfully.
2. **Given** a YAML configuration file with missing required fields, **When** the test framework attempts to load it, **Then** it reports clear validation errors identifying which fields are missing.
3. **Given** no YAML configuration file exists at the expected path, **When** the test framework starts, **Then** it skips integration tests gracefully with an informative message rather than failing.
4. **Given** a YAML configuration file with multiple target systems, **When** the framework parses it, **Then** each target system is available as a separate test context with its own OS type, hostname, and access credentials.

---

### User Story 2 - Payload Generation and Download (Priority: P2)

An operator triggers integration tests that generate agent payloads through the Mythic server for each configured agent type and C2 profile. The generated payloads are downloaded from Mythic and validated to ensure they were built successfully. This confirms that the Mythic server's payload generation pipeline is functional and that MythicMCP can orchestrate the build process.

**Why this priority**: Payloads must exist before they can be uploaded to target systems. This validates the first half of the end-to-end workflow.

**Independent Test**: Can be fully tested by requesting payload generation from the Mythic server for each configured agent type, downloading the resulting payload, and verifying the file is non-empty and matches expected characteristics (file size > 0, correct file extension).

**Acceptance Scenarios**:

1. **Given** a running Mythic server with an agent type installed (e.g., Apollo), **When** the test requests payload generation for that agent, **Then** a payload is created on the Mythic server and can be downloaded as a binary file.
2. **Given** a payload generation request for a configured agent and C2 profile, **When** the build completes, **Then** the downloaded payload file is non-empty and has the expected format.
3. **Given** a payload generation request for an agent type not installed on the Mythic server, **When** the test attempts generation, **Then** the test reports a clear failure indicating the agent type is unavailable.

---

### User Story 3 - Payload Upload and Execution on Target Systems (Priority: P3)

An operator runs integration tests that upload a previously generated payload to a configured target system and execute it. The test uses MythicMCP's file upload capabilities and agent tools to place the payload on the target and run it. This validates the upload pipeline and confirms that payloads can be delivered to target infrastructure.

**Why this priority**: Depends on payload generation (US2) being functional. Tests the critical delivery mechanism.

**Independent Test**: Can be tested by uploading a pre-built payload to a target system defined in the YAML configuration via an existing callback and verifying the file was placed at the expected path on the target.

**Acceptance Scenarios**:

1. **Given** a generated payload and a configured target system with an existing callback, **When** the test uploads the payload to the target via the existing callback, **Then** the file appears at the specified path on the target system.
2. **Given** a payload uploaded to a target system, **When** the test executes the payload on the target, **Then** the payload process starts on the target system.
3. **Given** a target system that is unreachable or whose callback has died, **When** the test attempts to upload a payload, **Then** the test reports a clear failure with the target system identifier and error details.

---

### User Story 4 - Callback Verification (Priority: P4)

After a payload is executed on a target system, the integration test verifies that a new callback appears in the Mythic server. The test polls the Mythic server for new callbacks matching the expected hostname and agent type, with a configurable timeout. This confirms the full agent-to-server communication path is working.

**Why this priority**: Depends on payload execution (US3). Validates the most critical outcome — that the agent successfully phones home.

**Independent Test**: Can be tested by checking for callbacks matching known criteria (hostname, agent type) after payload execution, with appropriate timeout and polling.

**Acceptance Scenarios**:

1. **Given** a payload has been executed on a target system, **When** the test polls for new callbacks, **Then** a new callback matching the target hostname and agent type appears within the configured timeout period.
2. **Given** a payload was executed but the callback does not appear, **When** the timeout period expires, **Then** the test reports a failure with details about what callback was expected and how long it waited.
3. **Given** multiple payloads executed on different target systems, **When** the test verifies callbacks, **Then** each target system's callback is independently verified.

---

### User Story 5 - Test Command Execution on Callbacks (Priority: P5)

After callback verification, the integration test executes a set of configured test commands on the new callback to validate that the agent is functioning correctly. Commands are defined in the YAML configuration and may vary by agent type and OS. The test verifies that commands complete successfully and return expected output patterns.

**Why this priority**: This is the final validation step. Depends on callback verification (US4) being successful.

**Independent Test**: Can be tested by executing pre-defined commands on an existing callback and verifying the output matches expected patterns defined in the configuration.

**Acceptance Scenarios**:

1. **Given** an active callback and configured test commands, **When** the test executes each command, **Then** each command completes within its timeout and returns output.
2. **Given** a test command with an expected output pattern, **When** the command executes, **Then** the output matches the expected pattern (substring or regex match).
3. **Given** a command that fails or times out, **When** the test records results, **Then** the failure is reported with the command, expected output, actual output (if any), and error details.

---

### Edge Cases

- What happens when the Mythic server is restarted mid-test? Tests should detect connection loss and report it clearly rather than hanging.
- What happens when a callback dies during command execution? The test should detect the callback status change and report which commands could not be completed.
- What happens when the YAML configuration references an agent type not installed on the Mythic server? The test should skip that agent's tests with a clear warning.
- What happens when a target lists an agent type that is incompatible with its OS? The test should report a configuration error before execution begins.
- What happens when multiple test runs execute concurrently? Each test run should use unique identifiers to avoid confusing callbacks from different runs.
- What happens when target system credentials in the YAML are incorrect? The test should fail fast with a clear authentication error rather than timing out.
- What happens when cleanup fails (e.g., callback died before payload could be removed)? Cleanup failures are logged as warnings but do not cause the test run to report failure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load test environment configuration from a fully self-contained YAML file located in the repository at a well-known path (default: `tests/integration/config.yaml`), including Mythic server connection details (URL, credentials).
- **FR-002**: System MUST validate the YAML configuration against a defined schema and report all validation errors before test execution begins.
- **FR-003**: System MUST support defining multiple target systems in the configuration, each with hostname, OS type, access details, and an explicit list of agent types to test on that target.
- **FR-004**: System MUST support defining multiple agent types to test, each with build parameters and C2 profile configuration.
- **FR-005**: System MUST generate payloads through the Mythic server API for each configured agent type and C2 profile combination.
- **FR-006**: System MUST download generated payloads from the Mythic server and validate they are non-empty.
- **FR-007**: System MUST upload payloads to target systems using existing callbacks and MythicMCP agent tools.
- **FR-008**: System MUST execute uploaded payloads on target systems via existing callbacks.
- **FR-009**: System MUST poll for new callbacks matching expected hostname (case-insensitive) and agent type, with a configurable timeout (default: 120 seconds).
- **FR-010**: System MUST execute configured test commands on verified callbacks and capture their output.
- **FR-011**: System MUST validate command output against expected patterns (substring or regex) defined in the configuration.
- **FR-012**: System MUST report per-test-step results including pass/fail status, timing, and error details.
- **FR-013**: System MUST structure tests as separate phases (generate, upload/execute, verify callback, run commands) per agent/target pair, where each phase is an independently reportable test.
- **FR-014**: System MUST skip later-phase tests when an earlier phase fails for the same agent/target pair, rather than running them and producing cascading failures.
- **FR-015**: System MUST skip integration tests gracefully when the YAML configuration file is absent or the Mythic server is unreachable.
- **FR-016**: System MUST support configurable timeouts for payload generation, callback verification, and command execution.
- **FR-017**: System MUST allow overriding the YAML configuration file path via the `MYTHICMCP_TEST_CONFIG` environment variable.
- **FR-018**: System MUST remove uploaded payload files from target systems after test commands complete.
- **FR-019**: System MUST deactivate any new callbacks created during the test run after all test commands for that callback have completed.
- **FR-020**: System MUST perform cleanup on a best-effort basis — cleanup failures are logged as warnings but do not cause the overall test run to fail.

### Key Entities

- **Test Configuration**: The top-level YAML document containing all configuration needed for a test run: Mythic server connection details (URL, credentials), target system definitions, agent configurations, and test commands. Fully self-contained — does not depend on external environment variables.
- **Target System**: A host where payloads will be uploaded and executed. Characterized by hostname, OS type, how it is accessed (via an existing callback ID or other mechanism), and an explicit list of agent types to test on it.
- **Agent Configuration**: Defines which agent type (e.g., Apollo, Arachne) to build, which C2 profile to use, and build-specific parameters.
- **Test Command**: A command to execute on a callback after verification, including the command string, expected output pattern, and timeout.
- **Test Run**: A single execution of the integration test suite, producing results for all configured agent/target combinations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All configured agent types can be built, deployed to target systems, and verified to call back within the configured timeout period.
- **SC-002**: All configured test commands execute on verified callbacks and produce output matching expected patterns.
- **SC-003**: A new target system or agent type can be added to testing by editing only the YAML configuration file, with no code changes required.
- **SC-004**: When any test step fails, the operator can identify the failure point (generation, upload, callback, command) and root cause from the test output alone.
- **SC-005**: Integration tests complete without manual intervention when given a valid configuration and reachable infrastructure.
- **SC-006**: Tests that cannot run due to missing configuration or unreachable servers are skipped with clear messages rather than producing false failures.

## Assumptions

- A running Mythic server (v3.3+) with at least one agent type installed is available during integration test execution.
- Target systems have existing callbacks established that can be used to upload and execute new payloads (the test does not establish initial access — it uses pre-existing callbacks).
- The test environment consists of two target systems: one running Debian Linux and one running Windows 11. The YAML sample configuration should reflect this two-system setup.
- The `mythic` Python package (0.2.10+) supports payload generation and download operations needed by the tests.
- Test commands defined in the YAML are appropriate for the target OS (the operator is responsible for configuring OS-appropriate commands).
- The YAML configuration file may contain sensitive information (credentials, tokens) and should be gitignored. A `config.sample.yaml` with placeholder values and inline comments explaining each field should be committed as a reference for operators.
