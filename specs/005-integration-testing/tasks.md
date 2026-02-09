# Tasks: Integration Testing Pipeline

**Input**: Design documents from `/specs/005-integration-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Tests are integration tests by nature — the entire feature is a test infrastructure.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and create project scaffolding for the integration test pipeline

- [x] T001 Add `pyyaml` as a dev dependency in pyproject.toml
- [x] T002 Add `tests/integration/config.yaml` to .gitignore
- [x] T003 Create tests/integration/__init__.py (empty, enables pytest discovery)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared Pydantic config models and test fixtures used by all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create Pydantic config models in tests/integration/config_models.py — implement `MythicConnectionConfig`, `TimeoutConfig`, `AgentConfig`, `C2ProfileConfig`, `BuildParam`, `TargetConfig`, `TestCommandConfig`, and `IntegrationTestConfig` per data-model.md schema. Include cross-validation: agent name references in targets must exist in agents list, test_commands keys must match agent names, agent OS must be compatible with target OS.
- [x] T005 Implement `load_integration_config()` function in tests/integration/config_models.py — load YAML with `yaml.safe_load()`, validate with `IntegrationTestConfig.model_validate()`, support `MYTHICMCP_TEST_CONFIG` env var override, fall back to `tests/integration/config.yaml`. Raise `FileNotFoundError` when config absent, `ValidationError` on schema violations.
- [x] T006 Create shared test state module in tests/integration/state.py — implement a module-level dictionary keyed by `(agent_name, target_name)` tuples storing `payload_uuid`, `payload_bytes`, `new_callback_id`, and `phase_results`. Include helper functions `set_phase_result(agent, target, phase, passed)` and `check_phase_passed(agent, target, phase)` for dependency checking.
- [x] T007 Create integration test fixtures in tests/integration/conftest.py — implement session-scoped `integration_config` fixture that loads config via `load_integration_config()` and skips all tests with `pytest.skip("Integration config not found")` if config file absent. Implement session-scoped `mythic_instance` fixture that connects to Mythic using config credentials via `mythic.login()` and skips with `pytest.skip("Mythic server unreachable")` on connection failure. Add `@pytest.mark.integration` marker to all fixtures.
- [x] T008 [P] Create config.sample.yaml in tests/integration/config.sample.yaml — include all sections (mythic, timeouts, agents, targets, test_commands) with placeholder values and inline comments explaining each field per data-model.md schema. Include two target systems (windows-target with os: Windows, linux-target with os: Linux) and two agents (apollo for Windows, arachne for Linux).

**Checkpoint**: Config loading, validation, shared state, and Mythic connection fixtures are ready. All user story test files can now use these.

---

## Phase 3: User Story 1 - YAML-Configured Test Environment (Priority: P1) 🎯 MVP

**Goal**: Operators define test environments in a YAML config file; the framework loads, validates, and rejects invalid configs with clear errors.

**Independent Test**: Load a sample YAML config and confirm all fields parse correctly; load invalid configs and confirm clear validation errors.

### Implementation for User Story 1

- [x] T009 [US1] Create unit tests for config loading in tests/unit/test_integration_config.py — test valid config loads all fields correctly, test missing required fields produce `ValidationError` with field names, test invalid agent references in targets produce cross-validation errors, test missing config file raises `FileNotFoundError`, test `MYTHICMCP_TEST_CONFIG` env var overrides default path, test OS compatibility validation (Windows agent on Linux target produces error), test empty agents/targets lists produce validation error, test duplicate agent names produce validation error.
- [x] T010 [US1] Create integration connection test in tests/integration/test_connection.py — add `test_mythic_connection_from_config` that loads the YAML config and connects to Mythic using the configured credentials, verifying the connection succeeds and an operation is set. Mark with `@pytest.mark.integration`.

**Checkpoint**: Config loading and validation is fully functional and testable without a Mythic server (unit tests) and with one (connection test).

---

## Phase 4: User Story 2 - Payload Generation and Download (Priority: P2)

**Goal**: Generate agent payloads through the Mythic API for each configured agent type and C2 profile, download them, and validate they are non-empty.

**Independent Test**: Request payload generation per configured agent, download the payload, verify file is non-empty.

**Dependencies**: Requires Phase 2 (config + Mythic connection) and Phase 3 (config validation). US2 → US3 (payloads needed before upload).

### Implementation for User Story 2

- [x] T011 [US2] Implement `generate_payload()` helper in tests/integration/helpers/payload.py — call `mythic.create_payload()` with agent config parameters (`payload_type_name`, `operating_system`, `c2_profiles`, `build_parameters`, `filename`) and `return_on_complete=True`. Validate `build_phase == "success"`, raise descriptive error with `build_message` and `build_stderr` on failure. Return payload UUID.
- [x] T012 [US2] Implement `download_payload()` helper in tests/integration/helpers/payload.py — call `mythic.download_payload(mythic_instance, payload_uuid)`, validate result is non-empty bytes, raise `PayloadDownloadError` if empty. Return raw bytes.
- [x] T013 [US2] Create tests/integration/helpers/__init__.py (empty, enables imports)
- [x] T014 [US2] Create payload generation tests in tests/integration/test_payload_generation.py — implement `test_generate_payload` parametrized by agent config from YAML. For each agent: call `generate_payload()`, store UUID in shared state via `state.py`, assert UUID is non-empty string. Implement `test_download_payload` parametrized by agent config: check `phase_results` for generation success (skip if failed), call `download_payload()`, store bytes in shared state, assert `len(payload_bytes) > 0`. Mark all with `@pytest.mark.integration`.

**Checkpoint**: Payloads can be generated and downloaded for all configured agents. Payload bytes are stored in shared state for US3.

---

## Phase 5: User Story 3 - Payload Upload and Execution (Priority: P3)

**Goal**: Upload generated payloads to target systems via existing callbacks and execute them.

**Independent Test**: Upload a payload to each configured target via its pre-existing callback and execute it.

**Dependencies**: Requires US2 (payload_bytes in shared state). US3 → US4 (execution triggers new callback).

### Implementation for User Story 3

- [x] T015 [US3] Implement `get_baseline_callback_ids()` helper in tests/integration/helpers/callback.py — call `mythic.get_all_active_callbacks()`, return `set` of all active callback `display_id` values. This captures the baseline before payload execution so new callbacks can be identified.
- [x] T016 [US3] Implement `upload_payload_to_target()` helper in tests/integration/helpers/deployment.py — register payload bytes with Mythic via `mythic.register_file()`, then issue upload task to the target's pre-existing callback (`target.callback_id`) using `mythic.issue_task()` with appropriate command based on target's agent type (Apollo: `upload` with file_id and remote_path; Arachne: `upload` with file_id and remote_path). Wait for task completion. Return file_id.
- [x] T017 [US3] Implement `execute_payload_on_target()` helper in tests/integration/helpers/deployment.py — determine execution command based on target OS (Windows: `shell` with upload_path; Linux: `shell` with `chmod +x path && path &`). Issue task to pre-existing callback. Wait for task acknowledgment (not completion — payload runs independently as a new process).
- [x] T018 [US3] Create deployment tests in tests/integration/test_payload_deployment.py — implement `test_upload_payload` parametrized by (agent, target) pairs from YAML config. Check `phase_results` for download success (skip if failed). Call `get_baseline_callback_ids()` and store in shared state. Call `upload_payload_to_target()`. Assert no exception. Implement `test_execute_payload` parametrized by (agent, target) pairs. Check upload phase success (skip if failed). Call `execute_payload_on_target()`. Record phase result. Mark all with `@pytest.mark.integration`.

**Checkpoint**: Payloads are uploaded and executed on all configured targets. Baseline callback IDs are captured for US4 filtering.

---

## Phase 6: User Story 4 - Callback Verification (Priority: P4)

**Goal**: Poll for new callbacks matching expected hostname and agent type after payload execution, with configurable timeout.

**Independent Test**: After execution, verify new callback appears matching target hostname and agent type within timeout.

**Dependencies**: Requires US3 (payload executed, baseline IDs captured). US4 → US5 (new callback_id needed for commands).

### Implementation for User Story 4

- [x] T019 [US4] Implement `wait_for_callback()` helper in tests/integration/helpers/callback.py — poll `mythic.get_all_active_callbacks()` at `polling_interval` (default 5s) up to `timeout` (default 120s). Filter by hostname (case-insensitive match) and agent type match (`payload.payloadtype.name`). Exclude callback IDs in `baseline_ids`. Return `display_id` of first match. Raise `TimeoutError` with expected criteria (hostname, agent type, waited duration) if no match found.
- [x] T020 [US4] Create callback verification tests in tests/integration/test_callback_verification.py — implement `test_verify_callback` parametrized by (agent, target) pairs. Check `phase_results` for execution success (skip if failed). Retrieve baseline IDs from shared state. Call `wait_for_callback()` with target hostname, agent payload_type, and configured timeouts. Store returned `new_callback_id` in shared state. Assert callback ID is a positive integer. Mark all with `@pytest.mark.integration`.

**Checkpoint**: New callbacks are verified for all agent/target pairs. Callback IDs are stored in shared state for US5.

---

## Phase 7: User Story 5 - Test Command Execution (Priority: P5)

**Goal**: Execute configured test commands on verified callbacks and validate output matches expected patterns.

**Independent Test**: Run each configured command on a callback and verify output contains expected substring.

**Dependencies**: Requires US4 (new_callback_id in shared state).

### Implementation for User Story 5

- [x] T021 [US5] Implement `execute_test_command()` helper in tests/integration/helpers/command.py — call `mythic.issue_task()` with `command_name`, `parameters`, `callback_display_id`, `wait_for_complete=True`, and `timeout`. Collect output via `mythic.get_all_task_output_by_id()`. If `expected_output` is set, first try `re.search(expected_output, output)` for regex matching; if the pattern is invalid regex, fall back to substring containment check. Return `(passed: bool, output: str)`.
- [x] T022 [US5] Create command execution tests in tests/integration/test_command_execution.py — implement `test_run_command` parametrized by (agent, target, command) triples from YAML config. Check `phase_results` for callback verification success (skip if failed). Retrieve `new_callback_id` from shared state. Call `execute_test_command()`. If `expected_output` defined, assert `passed` is True with message showing expected vs actual. If no `expected_output`, just assert command completed without error. Mark all with `@pytest.mark.integration`.

**Checkpoint**: All configured test commands execute and produce expected output on all verified callbacks.

---

## Phase 8: Cleanup

**Goal**: Remove uploaded payloads from targets and deactivate new callbacks after testing.

**Dependencies**: Runs after US5, uses shared state from US3 (upload_path) and US4 (new_callback_id).

### Implementation for Cleanup

- [x] T023 Implement `cleanup_payload_on_target()` helper in tests/integration/helpers/cleanup.py — determine delete command based on target OS (Windows: `del /f "upload_path"` via shell; Linux: `rm -f upload_path` via shell). Issue task to pre-existing callback (`target.callback_id`). Log warning on failure via `logging.warning()`. Return True/False success indicator.
- [x] T024 Implement `deactivate_callback()` helper in tests/integration/helpers/cleanup.py — call `mythic.update_callback(callback_display_id, active=False)`. Check response for success status. Log warning on failure. Return True/False.
- [x] T025 Create cleanup tests in tests/integration/test_cleanup.py — implement `test_cleanup_payload` parametrized by (agent, target) pairs. Retrieve upload_path from target config. Call `cleanup_payload_on_target()`. Assert returns True (but use `pytest.warns` or soft assertion — cleanup failures should not fail the test run per FR-020). Implement `test_deactivate_callback` parametrized by (agent, target) pairs. Retrieve `new_callback_id` from shared state. Skip if no callback was created. Call `deactivate_callback()`. Assert returns True (soft assertion). Mark all with `@pytest.mark.integration`.

**Checkpoint**: All payloads removed from targets and new callbacks deactivated.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and integration run script

- [x] T026 [P] Update scripts/run_integration_tests.sh to add a `--pipeline` flag that runs `pytest tests/integration/ -v -m integration` for the full end-to-end pipeline
- [x] T027 [P] Update .claude/agents/test-runner.md to document the integration test pipeline and how to run it (`uv run pytest tests/integration/ -v -m integration`)
- [x] T028 Run full pipeline validation per quickstart.md — execute `uv run pytest tests/unit/test_integration_config.py -v` for config validation, then `uv run pytest tests/integration/ -v -m integration` for full pipeline. Verify output matches expected format from quickstart.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — config validation tests
- **US2 (Phase 4)**: Depends on Foundational — payload generation (can run parallel to US1)
- **US3 (Phase 5)**: Depends on US2 — needs payload bytes
- **US4 (Phase 6)**: Depends on US3 — needs payload executed + baseline IDs
- **US5 (Phase 7)**: Depends on US4 — needs new callback ID
- **Cleanup (Phase 8)**: Depends on US5 — runs after all commands complete
- **Polish (Phase 9)**: Depends on all phases complete

### User Story Dependencies

```
US1 (config) ─────────────────────────────────── (independent)
US2 (payload gen) → US3 (upload/exec) → US4 (callback) → US5 (commands) → Cleanup
```

- **US1** is fully independent — can be implemented and tested without Mythic targets
- **US2–US5 + Cleanup** form a sequential chain — each phase depends on the prior phase's shared state

### Within Each User Story

- Helpers before test files
- Shared state setup before consumers

### Parallel Opportunities

- T001, T002, T003 (Setup phase) — all independent
- T004, T005, T006, T007, T008 — T008 (sample config) is parallel; T004-T007 are sequential
- T009, T010 (US1) — parallel (unit vs integration)
- T011, T012, T013 (US2 helpers) — T011/T012 sequential, T013 parallel
- T015, T016, T017 (US3 helpers) — T015 parallel with T016/T017
- T023, T024 (cleanup helpers) — parallel
- T026, T027 (polish) — parallel

---

## Parallel Example: Foundational Phase

```bash
# These can run in parallel:
Task: "Create config.sample.yaml in tests/integration/config.sample.yaml"  # T008
Task: "Create shared test state module in tests/integration/state.py"      # T006

# These must be sequential:
Task: "Create Pydantic config models in tests/integration/config_models.py" # T004
Task: "Implement load_integration_config() in tests/integration/config_models.py" # T005 (depends on T004)
Task: "Create integration test fixtures in tests/integration/conftest.py"   # T007 (depends on T005)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (config models + fixtures)
3. Complete Phase 3: US1 (config validation tests)
4. **STOP and VALIDATE**: Run `uv run pytest tests/unit/test_integration_config.py -v`
5. Config loading, validation, and error handling are verified

### Incremental Delivery

1. Setup + Foundational → Config models and fixtures ready
2. Add US1 → Config validation verified (MVP!)
3. Add US2 → Payload generation and download verified
4. Add US3 → Upload and execution verified
5. Add US4 → Callback verification verified
6. Add US5 → Command execution verified
7. Add Cleanup → Full pipeline with cleanup
8. Polish → Scripts and docs updated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2–US5 form a sequential pipeline — each depends on prior phase's shared state
- US1 is fully independent and serves as the MVP
- All integration tests use `@pytest.mark.integration` marker
- Cleanup tests use soft assertions — failures warn but don't fail the run
- Commit after each phase checkpoint
