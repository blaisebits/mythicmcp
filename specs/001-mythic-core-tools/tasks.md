# Tasks: Mythic Framework Core Tools

**Input**: Design documents from `/specs/001-mythic-core-tools/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/mythicmcp/`, `tests/` at repository root (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Python package structure

- [x] T001 Create project directory structure per plan.md in src/mythicmcp/
- [x] T002 Initialize Python project with pyproject.toml including mcp, mythic, pydantic dependencies
- [x] T003 [P] Create src/mythicmcp/__init__.py with package metadata
- [x] T004 [P] Create tests/conftest.py with shared pytest fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement configuration management in src/mythicmcp/config.py with environment variable handling (MYTHIC_SERVER_URL, MYTHIC_API_TOKEN, MYTHIC_USERNAME, MYTHIC_PASSWORD)
- [x] T006 [P] Implement Mythic connection lifecycle in src/mythicmcp/connection.py with lifespan context manager
- [x] T007 [P] Create FastMCP server entry point in src/mythicmcp/server.py with lifespan integration
- [x] T008 Create src/mythicmcp/tools/__init__.py to export all tool modules
- [x] T009 Implement Pydantic response models in src/mythicmcp/models.py for Callback, Operation, Operator, and ConnectionStatus entities

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Active Callbacks (Priority: P1) 🎯 MVP

**Goal**: Operators can see all active callbacks in their Mythic operation with host details, agent type, and last check-in time

**Independent Test**: Connect to Mythic instance with at least one callback and verify tool returns callback data in expected format

### Implementation for User Story 1

- [x] T010 [US1] Implement core_list_callbacks tool in src/mythicmcp/tools/callbacks.py with GraphQL query to fetch active callbacks
- [x] T011 [US1] Add ListCallbacksResponse Pydantic model with callbacks array, count, and retrieved_at timestamp
- [x] T012 [US1] Add error handling for authentication errors, connection errors, and "no operation set" errors with descriptive messages
- [x] T013 [US1] Wire core_list_callbacks tool to FastMCP server in src/mythicmcp/server.py

**Checkpoint**: At this point, User Story 1 should be fully functional - operators can list all active callbacks

---

## Phase 4: User Story 4 - Retrieve Callback Details (Priority: P2)

**Goal**: Operators can see detailed information about a specific callback including full configuration, integrity level, and process info

**Independent Test**: Request details for a known callback ID and verify all expected fields are returned

### Implementation for User Story 4

- [x] T014 [US4] Implement core_get_callback tool in src/mythicmcp/tools/callbacks.py with callback_id parameter
- [x] T015 [US4] Add custom GraphQL query to fetch single callback by ID with full field set (domain, external_ip, architecture, process_id, description)
- [x] T016 [US4] Add GetCallbackResponse Pydantic model with full callback details and retrieved_at timestamp
- [x] T017 [US4] Add error handling for "callback not found" and "access denied" errors with clear messages
- [x] T018 [US4] Wire core_get_callback tool to FastMCP server in src/mythicmcp/server.py

**Checkpoint**: At this point, User Stories 1 AND 4 should both work - operators can list callbacks and drill into details

---

## Phase 5: User Story 2 - View Operation Details (Priority: P2)

**Goal**: Operators can see current operation context including name, creation date, and assigned operators

**Independent Test**: Connect to Mythic instance and retrieve operation metadata including operator list

### Implementation for User Story 2

- [x] T019 [P] [US2] Implement core_get_operation tool in src/mythicmcp/tools/operations.py with optional operation_id parameter
- [x] T020 [US2] Add GraphQL query to fetch operation details with operator list
- [x] T021 [US2] Add GetOperationResponse Pydantic model with operation details, operators array, and retrieved_at timestamp
- [x] T022 [US2] Add error handling for "operation not found" and "no current operation" errors
- [x] T023 [US2] Wire core_get_operation tool to FastMCP server in src/mythicmcp/server.py

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should all work independently

---

## Phase 6: User Story 3 - Check Mythic Server Status (Priority: P3)

**Goal**: Operators can verify Mythic server connectivity and authentication before performing operations

**Independent Test**: Point at valid and invalid Mythic server addresses and verify appropriate success/error responses

### Implementation for User Story 3

- [x] T024 [P] [US3] Implement core_check_connection tool in src/mythicmcp/tools/status.py
- [x] T025 [US3] Add CheckConnectionResponse Pydantic model with connected, server_url, authenticated, current_operation, and timestamp fields
- [x] T026 [US3] Add error response handling that distinguishes connection_failed, authentication_failed, and timeout errors
- [x] T027 [US3] Wire core_check_connection tool to FastMCP server in src/mythicmcp/server.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and security hardening

- [x] T028 [P] Verify FR-006 compliance: audit all error messages and logs for credential exposure
- [x] T029 [P] Verify FR-008 compliance: confirm all responses include retrieved_at/timestamp fields
- [x] T030 [P] Verify FR-009 compliance: confirm all tool descriptions clearly state Mythic operations
- [x] T031 Run quickstart.md validation - test installation and all four tools
- [x] T032 Validate Constitution Principle V: verify startup fails if credentials are invalid

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - US1 and US4 share callbacks.py but have distinct functions
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after US1 (shares callbacks.py module, builds on same infrastructure)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Separate module, independent of US1/US4
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Separate module, independent of all others

### Within Each User Story

- Tool implementation before response models (can be parallel if different files)
- Error handling after core implementation
- Wire to server after tool is complete

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 and T004 can run in parallel

**Phase 2 (Foundational)**:
- T006 and T007 can run in parallel after T005

**User Stories** (after Foundational completes):
- US2 (Phase 5) can run in parallel with US1/US4 (Phases 3-4) - different module (operations.py)
- US3 (Phase 6) can run in parallel with all others - different module (status.py)

**Phase 7 (Polish)**:
- T028, T029, T030 can all run in parallel

---

## Parallel Example: Foundational Phase

```bash
# After T005 (config.py) completes:
Task: "T006 Implement Mythic connection lifecycle in src/mythicmcp/connection.py"
Task: "T007 Create FastMCP server entry point in src/mythicmcp/server.py"
```

## Parallel Example: User Stories

```bash
# After Foundational phase completes, these can run in parallel:
# Developer A: User Story 1 (callbacks.py - list)
Task: "T010 [US1] Implement core_list_callbacks tool in src/mythicmcp/tools/callbacks.py"

# Developer B: User Story 2 (operations.py)
Task: "T019 [US2] Implement core_get_operation tool in src/mythicmcp/tools/operations.py"

# Developer C: User Story 3 (status.py)
Task: "T024 [US3] Implement core_check_connection tool in src/mythicmcp/tools/status.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (core_list_callbacks)
4. **STOP and VALIDATE**: Test listing callbacks against real Mythic server
5. Deploy/demo if ready - operators can see their callbacks

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (list callbacks) → Test → Deploy (MVP!)
3. Add User Story 4 (callback details) → Test → Deploy (drill-down capability)
4. Add User Story 2 (operation info) → Test → Deploy (operation context)
5. Add User Story 3 (connection check) → Test → Deploy (diagnostics)
6. Each story adds value without breaking previous stories

### Recommended Execution Order

For a single developer working sequentially:

1. **Setup**: T001 → T002 → (T003 ∥ T004)
2. **Foundational**: T005 → (T006 ∥ T007) → T008 → T009
3. **US1 (MVP)**: T010 → T011 → T012 → T013 ✓ Validate
4. **US4**: T014 → T015 → T016 → T017 → T018 ✓ Validate
5. **US2**: T019 → T020 → T021 → T022 → T023 ✓ Validate
6. **US3**: T024 → T025 → T026 → T027 ✓ Validate
7. **Polish**: (T028 ∥ T029 ∥ T030) → T031 → T032

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- US4 is listed after US1 despite both being P2 because they share callbacks.py
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All timestamps must be ISO 8601 format with UTC timezone per FR-008
- All error messages must never expose credentials per FR-006
