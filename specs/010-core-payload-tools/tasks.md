# Tasks: Core Payload Tools

**Input**: Design documents from `/specs/010-core-payload-tools/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story. Each story is independently testable after completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Create module skeleton and shared infrastructure

- [ ] T001 Create `src/mythicmcp/tools/payloads.py` with module docstring, imports (`logging`, `base64`, `TYPE_CHECKING`), and exception class hierarchy: `PayloadError` (base), `PayloadNotFoundError`, `NoOperationError`, `PayloadBuildError`, `PayloadDownloadError`, `InvalidJSONError`, `ConnectionError`. Follow pattern from `src/mythicmcp/tools/files.py` exception classes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared Pydantic models that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add payload entity models to `src/mythicmcp/models.py`: `C2ProfileSummary` (name, is_p2p, running), `PayloadSummary` (uuid, agent_type, build_phase, description, deleted, auto_generated, creation_time, os, c2_profiles), and `PayloadDetail` (extends summary with build_message, build_stderr, callback_alert, operator, file_uuid, filename, os). Use Field descriptions and Optional types per existing model patterns. See `data-model.md` for field mappings.
- [ ] T003 Add payload response models to `src/mythicmcp/models.py`: `ListPayloadsResponse` (payloads, count, retrieved_at), `GetPayloadResponse` (payload, retrieved_at), `CreatePayloadResponse` (success, uuid, build_phase, build_message, retrieved_at), `CreatePayloadErrorResponse` (success=False, error, error_type, uuid optional, retrieved_at), `DownloadPayloadResponse` (success, payload_uuid, filename, content, size_bytes, retrieved_at), `DownloadPayloadErrorResponse` (success=False, error, error_type, payload_uuid, retrieved_at), `PayloadConfigCheckResponse` (payload_uuid, status, error, output, retrieved_at). Follow `utc_now` default_factory pattern from existing models.

**Checkpoint**: All models available. User story implementation can begin.

---

## Phase 3: User Story 1 - List All Payloads (Priority: P1) MVP

**Goal**: Operators can list all payloads in current operation with UUID, agent type, build status, C2 profiles.

**Independent Test**: Call `core_list_payloads` on an operation with payloads. Verify returned list matches Mythic UI. Call with no operation set — verify error.

### Implementation for User Story 1

- [ ] T004 [US1] Implement `_parse_c2_profile_summary()` and `_parse_payload_summary()` helper functions in `src/mythicmcp/tools/payloads.py`. Parse nested GraphQL response structures (payloadtype.name, payloadc2profiles) into `C2ProfileSummary` and `PayloadSummary` Pydantic models. Follow `_parse_callback_summary()` pattern from `callbacks.py`.
- [ ] T005 [US1] Implement `list_payloads()` async function in `src/mythicmcp/tools/payloads.py`. Use `mythic.get_all_payloads()` with custom lightweight `custom_return_attributes` string (uuid, build_phase, description, deleted, auto_generated, creation_time, os, payloadtype{name}, payloadc2profiles{c2profile{name,running,is_p2p}}). Check `current_operation_id` first. Return `ListPayloadsResponse`. Raise `NoOperationError` or `ConnectionError`.
- [ ] T006 [US1] Implement `core_list_payloads()` entry point in `src/mythicmcp/tools/payloads.py`. Get `MythicContext` from `ctx.request_context.lifespan_context`. Catch exceptions and raise `McpError` (matching `callbacks.py` pattern for read-only tools).
- [ ] T007 [US1] Register `core_list_payloads` in `src/mythicmcp/server.py` with `@mcp.tool()` decorator under a new `# --- Payload Tools ---` section. Add import and export in `src/mythicmcp/tools/__init__.py`.

**Checkpoint**: `core_list_payloads` functional. Can list all payloads in current operation.

---

## Phase 4: User Story 2 - Get Payload Details (Priority: P1)

**Goal**: Operators can inspect a specific payload's full configuration, build output, and file metadata by UUID.

**Independent Test**: Call `core_get_payload` with a known payload UUID. Verify all detail fields returned. Call with invalid UUID — verify not-found error.

### Implementation for User Story 2

- [ ] T008 [US2] Implement `_parse_payload_detail()` helper in `src/mythicmcp/tools/payloads.py`. Parse full GraphQL response into `PayloadDetail` model including build_message, build_stderr, operator.username, filemetum fields, and os. Reuse `_parse_c2_profile_summary()` from US1.
- [ ] T009 [US2] Implement `get_payload_by_uuid()` async function in `src/mythicmcp/tools/payloads.py`. Use `mythic.get_payload_by_uuid()` with default `payload_data_fragment` attributes. Check `current_operation_id`. Return `GetPayloadResponse`. Raise `PayloadNotFoundError` on empty result or `NoOperationError`.
- [ ] T010 [US2] Implement `core_get_payload()` entry point in `src/mythicmcp/tools/payloads.py` with `payload_uuid: str` parameter. Catch exceptions and raise `McpError`.
- [ ] T011 [US2] Register `core_get_payload` in `src/mythicmcp/server.py` and add export in `src/mythicmcp/tools/__init__.py`.

**Checkpoint**: `core_list_payloads` + `core_get_payload` functional. Operators can discover and inspect payloads.

---

## Phase 5: User Story 3 - Create a Payload (Priority: P2)

**Goal**: Operators can create a new standard payload with agent type, OS, C2 config, and receive build results.

**Independent Test**: Call `core_create_payload` with valid Apollo/Poseidon config. Verify UUID and build_phase returned. Call with invalid agent type — verify error. Call with malformed JSON — verify invalid_input error.

### Implementation for User Story 3

- [ ] T012 [US3] Implement JSON input parsing helpers in `src/mythicmcp/tools/payloads.py`: `_parse_c2_profiles_json(json_str) -> list[dict]` validates structure `[{c2_profile: str, c2_profile_parameters: dict}]`; `_parse_build_parameters_json(json_str) -> list[dict]` validates `[{name: str, value: str}]`; `_parse_commands_json(json_str) -> list[str]`. Each raises `InvalidJSONError` with descriptive message on parse failure. Empty string input returns empty list.
- [ ] T013 [US3] Implement `create_payload()` async function in `src/mythicmcp/tools/payloads.py`. Call `mythic.create_payload()` with parsed params, `return_on_complete=True`, and caller-provided timeout. Handle build success (build_phase == "success") and failure. Return `CreatePayloadResponse` on success. Raise `PayloadBuildError` (with UUID) on build failure, `NoOperationError`, `ConnectionError`. Handle `asyncio.TimeoutError` by returning error with UUID if available.
- [ ] T014 [US3] Implement `core_create_payload()` entry point in `src/mythicmcp/tools/payloads.py` with parameters: `payload_type_name: str`, `filename: str`, `operating_system: str`, `c2_profiles: str` (JSON), `description: str = ""`, `commands: str = ""` (JSON), `build_parameters: str = ""` (JSON), `include_all_commands: bool = False`, `timeout: int = 300`. Validate timeout range (30-600). Parse JSON inputs. Return `CreatePayloadResponse | CreatePayloadErrorResponse` (matching `files.py` union pattern).
- [ ] T015 [US3] Register `core_create_payload` in `src/mythicmcp/server.py` and add export in `src/mythicmcp/tools/__init__.py`.

**Checkpoint**: Can create, list, and inspect payloads. Core payload lifecycle operational.

---

## Phase 6: User Story 4 - Download a Payload (Priority: P2)

**Goal**: Operators can download a built payload binary as base64-encoded content.

**Independent Test**: Call `core_download_payload` with a successfully built payload UUID. Verify non-empty base64 content, filename, and size. Call with failed-build UUID — verify build_incomplete error.

### Implementation for User Story 4

- [ ] T016 [US4] Implement `download_payload()` async function in `src/mythicmcp/tools/payloads.py`. First call `mythic.get_payload_by_uuid()` to verify payload exists and check `build_phase == "success"`. Then call `mythic.download_payload()` to get bytes. Base64-encode content. Return `DownloadPayloadResponse` with payload_uuid, filename (from filemetum), content, size_bytes. Raise `PayloadNotFoundError`, `PayloadDownloadError` (build incomplete), `NoOperationError`, `ConnectionError`.
- [ ] T017 [US4] Implement `core_download_payload()` entry point in `src/mythicmcp/tools/payloads.py` with `payload_uuid: str` parameter. Return `DownloadPayloadResponse | DownloadPayloadErrorResponse` (union pattern matching `core_download_file`).
- [ ] T018 [US4] Register `core_download_payload` in `src/mythicmcp/server.py` and add export in `src/mythicmcp/tools/__init__.py`.

**Checkpoint**: Full payload lifecycle: list, inspect, create, download.

---

## Phase 7: User Story 5 - Config Check + User Story 6 - Redirect Rules (Priority: P3)

**Goal**: Operators can validate payload C2 config and retrieve redirect rules.

**Independent Test (US5)**: Call `core_check_payload_config` with a payload UUID. Verify status/output returned.
**Independent Test (US6)**: Call `core_payload_redirect_rules` with a payload UUID. Verify rules output returned.

### Implementation for User Stories 5 & 6

- [ ] T019 [P] [US5] Implement `check_payload_config()` async function in `src/mythicmcp/tools/payloads.py`. Call `mythic.payload_check_config()` with payload_uuid. Return `PayloadConfigCheckResponse`. Raise `PayloadNotFoundError`, `NoOperationError`, `ConnectionError`.
- [ ] T020 [P] [US6] Implement `payload_redirect_rules()` async function in `src/mythicmcp/tools/payloads.py`. Call `mythic.payload_redirect_rules()` with payload_uuid. Return `PayloadConfigCheckResponse`. Raise `PayloadNotFoundError`, `NoOperationError`, `ConnectionError`.
- [ ] T021 [US5] Implement `core_check_payload_config()` entry point in `src/mythicmcp/tools/payloads.py` with `payload_uuid: str`. Catch exceptions and raise `McpError`.
- [ ] T022 [US6] Implement `core_payload_redirect_rules()` entry point in `src/mythicmcp/tools/payloads.py` with `payload_uuid: str`. Catch exceptions and raise `McpError`.
- [ ] T023 Register `core_check_payload_config` and `core_payload_redirect_rules` in `src/mythicmcp/server.py` and add exports in `src/mythicmcp/tools/__init__.py`.

**Checkpoint**: All 6 payload tools operational.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Tests, documentation, and final validation

- [ ] T024 [P] Create `tests/unit/test_payload_tools.py` with tool registration tests: verify all 6 payload tools (`core_list_payloads`, `core_get_payload`, `core_create_payload`, `core_download_payload`, `core_check_payload_config`, `core_payload_redirect_rules`) are registered in mcp server, have descriptions, and have correct parameter signatures. Follow pattern from `tests/unit/test_file_tools.py`.
- [ ] T025 [P] Add unit tests for Pydantic model validation in `tests/unit/test_payload_tools.py`: test `PayloadSummary`, `PayloadDetail`, `C2ProfileSummary` construction with valid data; test response models include `retrieved_at` timestamp; test `CreatePayloadErrorResponse` accepts optional uuid. Follow pattern from `tests/unit/test_models.py`.
- [ ] T026 [P] Update Core Tools section in `CLAUDE.md` with new payload tools: `core_list_payloads`, `core_get_payload`, `core_create_payload`, `core_download_payload`, `core_check_payload_config`, `core_payload_redirect_rules` with brief descriptions.
- [ ] T027 Run full unit test suite (`pytest tests/unit/`) to verify no regressions and all new tests pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on Phase 2 (reuses US1 parser helpers but can proceed independently)
- **US3 (Phase 5)**: Depends on Phase 2
- **US4 (Phase 6)**: Depends on Phase 2 (uses get_payload_by_uuid from US2 internally, but implements its own)
- **US5+US6 (Phase 7)**: Depends on Phase 2
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories
- **US2 (P1)**: Reuses `_parse_c2_profile_summary()` from US1 — implement after or alongside US1
- **US3 (P2)**: Independent of US1/US2
- **US4 (P2)**: Independent (calls Mythic API directly, not through US2's function)
- **US5 (P3)**: Independent
- **US6 (P3)**: Independent, parallelizable with US5

### Within Each User Story

- Parsers/helpers before business logic
- Business logic before entry points
- Entry points before server registration

### Parallel Opportunities

- T002 and T003 are sequential (same file)
- T019 and T020 are parallel (independent functions, same file but different locations)
- T024, T025, T026 are parallel (different files)
- US1 and US3 can run in parallel (different tools, independent logic)
- US5 and US6 can run in parallel (nearly identical structure)

---

## Parallel Example: User Stories 5 & 6

```bash
# These can be implemented simultaneously:
Task T019: "Implement check_payload_config() in src/mythicmcp/tools/payloads.py"
Task T020: "Implement payload_redirect_rules() in src/mythicmcp/tools/payloads.py"

# Then sequentially:
Task T021: "Implement core_check_payload_config() entry point"
Task T022: "Implement core_payload_redirect_rules() entry point"
Task T023: "Register both tools in server.py and __init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002, T003)
3. Complete Phase 3: US1 - List Payloads (T004–T007)
4. **STOP and VALIDATE**: Verify `core_list_payloads` returns payload data
5. Functional read-only payload visibility

### Incremental Delivery

1. Setup + Foundational → Models and module ready
2. US1 (List) + US2 (Get) → Read-only payload inspection (MVP)
3. US3 (Create) + US4 (Download) → Full payload lifecycle
4. US5 (Config Check) + US6 (Redirect Rules) → Operational validation tools
5. Polish → Tests, docs, validation

### Suggested Execution Order (Single Developer)

Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → US5+US6 → Polish

---

## Notes

- All 6 tools modify `src/mythicmcp/tools/payloads.py` — sequential within a story, but story phases can be done in sequence
- `server.py` and `__init__.py` changes are small per-tool additions — can batch at end of each story
- US5 and US6 share `PayloadConfigCheckResponse` and nearly identical logic — implement together
- JSON string parsing (US3) is the most complex part — test with malformed input
- No integration tests in this feature — integration test infrastructure exists separately
