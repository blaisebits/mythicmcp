# Tasks: Core File Management Tools

**Input**: Design documents from `/specs/004-core-file-tools/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/mcp-tools.md, research.md

**Tests**: Integration tests included (pytest against Mythic instance per plan.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/mythicmcp/`, `tests/integration/` at repository root

---

## Phase 1: Setup

**Purpose**: No setup needed - extending existing MCP server

> This feature extends an existing codebase. No project initialization required.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add Pydantic models that all file tools depend on

**⚠️ CRITICAL**: Models must be complete before any user story implementation

- [X] T001 Add UploadFileResponse and UploadFileErrorResponse models in src/mythicmcp/models.py
- [X] T002 Add DownloadFileResponse and DownloadFileErrorResponse models in src/mythicmcp/models.py
- [X] T003 Add DownloadedFileSummary and ListDownloadedFilesResponse models in src/mythicmcp/models.py
- [X] T004 Add UploadedFileSummary and ListUploadedFilesResponse models in src/mythicmcp/models.py
- [X] T005 Add FileError exception classes with descriptive messages in src/mythicmcp/tools/files.py:
      - FileNotFoundError: "File with UUID {uuid} not found in current operation"
      - FileUploadError: "Failed to upload file '{filename}': {reason}"
      - InvalidBase64Error: "Invalid base64-encoded content: {details}"
      - NoOperationError: "No current operation set. Use core_set_operation first."
      - ConnectionError: "Failed to connect to Mythic server: {details}"

**Checkpoint**: All response models ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Upload File for Tasking (Priority: P1) 🎯 MVP

**Goal**: Operators can upload files to Mythic server and receive file_id for agent tasking

**Independent Test**: Upload a test file, verify file_id returned, confirm file appears in uploaded files list

### Implementation for User Story 1

- [X] T006 [US1] Implement upload_file() helper function wrapping mythic.register_file() in src/mythicmcp/tools/files.py
- [X] T007 [US1] Implement core_upload_file tool entry point in src/mythicmcp/tools/files.py
- [X] T008 [US1] Add base64 decoding with error handling for invalid content in src/mythicmcp/tools/files.py
- [X] T009 [US1] Register core_upload_file tool in src/mythicmcp/server.py

**Checkpoint**: User Story 1 complete - operators can upload files and get file_id

---

## Phase 4: User Story 2 - Download File from Mythic Server (Priority: P1)

**Goal**: Operators can download file content from Mythic by UUID

**Independent Test**: Download a known file UUID, verify base64 content returned with correct metadata

### Implementation for User Story 2

- [X] T010 [US2] Implement download_file() helper function wrapping mythic.download_file() in src/mythicmcp/tools/files.py
- [X] T011 [US2] Implement core_download_file tool entry point in src/mythicmcp/tools/files.py
- [X] T012 [US2] Add file metadata lookup (filename, hashes) via GraphQL query in src/mythicmcp/tools/files.py
- [X] T013 [US2] Register core_download_file tool in src/mythicmcp/server.py

**Checkpoint**: User Story 2 complete - operators can download file content by UUID

---

## Phase 5: User Story 3 - List Downloaded Files (Priority: P2)

**Goal**: Operators can see all files downloaded from agents in current operation

**Independent Test**: List downloaded files, verify response includes expected metadata fields (filename, callback_id, timestamp)

### Implementation for User Story 3

- [X] T014 [US3] Implement list_downloaded_files() helper wrapping mythic.get_all_downloaded_files() in src/mythicmcp/tools/files.py
- [X] T015 [US3] Add custom GraphQL attributes for callback info (callback_id, display_id) in src/mythicmcp/tools/files.py
- [X] T016 [US3] Implement core_list_downloaded_files tool entry point in src/mythicmcp/tools/files.py
- [X] T017 [US3] Register core_list_downloaded_files tool in src/mythicmcp/server.py

**Checkpoint**: User Story 3 complete - operators can list downloaded files with callback context

---

## Phase 6: User Story 4 - List Uploaded Files (Priority: P2)

**Goal**: Operators can see all files uploaded to Mythic in current operation

**Independent Test**: List uploaded files, verify response includes file_id, filename, operator, timestamp

### Implementation for User Story 4

- [X] T018 [US4] Implement list_uploaded_files() helper wrapping mythic.get_all_uploaded_files() in src/mythicmcp/tools/files.py
- [X] T019 [US4] Implement core_list_uploaded_files tool entry point in src/mythicmcp/tools/files.py
- [X] T020 [US4] Register core_list_uploaded_files tool in src/mythicmcp/server.py
- [X] T020a Verify all file tool error paths return structured error responses with error_type field in src/mythicmcp/tools/files.py

**Checkpoint**: User Story 4 complete - operators can list uploaded files with file_ids for tasking

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration tests, documentation, validation

- [X] T021 [P] Create integration test file tests/integration/test_file_tools.py
- [X] T022 [P] Add integration test for core_upload_file in tests/integration/test_file_tools.py
- [X] T023 [P] Add integration test for core_download_file in tests/integration/test_file_tools.py
- [X] T024 [P] Add integration test for core_list_downloaded_files in tests/integration/test_file_tools.py
- [X] T025 [P] Add integration test for core_list_uploaded_files in tests/integration/test_file_tools.py
- [X] T026 Update CLAUDE.md with new tools and recent changes
- [ ] T027 Run quickstart.md validation scenarios manually

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A - using existing project
- **Foundational (Phase 2)**: No dependencies - add models first
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority and independent
  - US3 and US4 are both P2 priority and independent
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational - No dependencies on other stories

All user stories share the same `src/mythicmcp/tools/files.py` file, so within each story, tasks are sequential. However, stories themselves can be interleaved.

### Within Each User Story

- Helper function before tool entry point
- Tool entry point before server registration
- All tasks in one story complete before checkpoint

### Parallel Opportunities

- Foundational model tasks (T001-T004) are sequential (same file)
- All Polish integration test tasks (T021-T025) can run in parallel
- User stories are conceptually independent but share files.py

---

## Sequential Example: Foundational Phase

```bash
# Execute model tasks in sequence (same file):
# T001 → T002 → T003 → T004
```

## Parallel Example: Integration Tests

```bash
# Launch all integration test tasks together:
Task: "Add integration test for core_upload_file in tests/integration/test_file_tools.py"
Task: "Add integration test for core_download_file in tests/integration/test_file_tools.py"
Task: "Add integration test for core_list_downloaded_files in tests/integration/test_file_tools.py"
Task: "Add integration test for core_list_uploaded_files in tests/integration/test_file_tools.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (models)
2. Complete Phase 3: User Story 1 (upload)
3. **STOP and VALIDATE**: Test upload with a real file
4. Operator can now upload files for agent tasking

### Incremental Delivery

1. Foundational → Models ready
2. Add User Story 1 (upload) → Test → Operators can upload files
3. Add User Story 2 (download) → Test → Operators can retrieve files
4. Add User Story 3 (list downloaded) → Test → Full visibility into agent downloads
5. Add User Story 4 (list uploaded) → Test → Full visibility into uploaded tools
6. Polish → Integration tests, documentation

### Recommended Order

Since US1 and US2 are both P1 priority:
1. Complete Foundational
2. Complete US1 (upload) - enables file deployment workflow
3. Complete US2 (download) - enables file retrieval workflow
4. Complete US3 and US4 (list) - provides operational visibility
5. Complete Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All 4 user stories are independent - each can be tested on its own
- Verify tests fail before implementing (if following TDD)
- Commit after each task or logical group
- All file tools go in single files.py module following existing patterns
