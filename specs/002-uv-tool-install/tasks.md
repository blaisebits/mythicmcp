# Tasks: UV Tool Installation Support

**Input**: Design documents from `/specs/002-uv-tool-install/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: No test tasks included - not explicitly requested in feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Verification)

**Purpose**: Verify existing infrastructure is correctly configured for uv tool installation

- [ ] T001 Verify pyproject.toml has correct [project.scripts] entry point
- [ ] T002 Verify hatchling build backend is properly configured in pyproject.toml
- [ ] T003 Test local installation with `uv tool install .` from repository root

---

## Phase 2: Foundational (No blocking prerequisites needed)

**Purpose**: The project already has foundational infrastructure. This feature only enhances documentation and UX.

**✅ SKIPPED**: No blocking foundational work required. User story work can begin immediately after Setup verification.

---

## Phase 3: User Story 1 - Install MythicMCP as a Global Tool (Priority: P1) 🎯 MVP

**Goal**: Enable one-command installation via `uv tool install mythicmcp`

**Independent Test**: Run `uv tool install .` on a clean system and verify `mythicmcp` command is available globally

### Implementation for User Story 1

- [ ] T004 [US1] Add project.urls metadata to pyproject.toml for repository and documentation links
- [ ] T005 [US1] Update README.md with uv tool installation instructions in README.md
- [ ] T006 [US1] Add installation verification steps to README.md
- [ ] T007 [US1] Test upgrade workflow with `uv tool install --upgrade .`

**Checkpoint**: Users can install MythicMCP with a single command and verify it's available

---

## Phase 4: User Story 2 - Configure MythicMCP After Installation (Priority: P2)

**Goal**: Provide clear configuration guidance when tool is run without proper setup

**Independent Test**: Run `mythicmcp` without environment variables configured and verify helpful guidance is displayed

### Implementation for User Story 2

- [ ] T008 [US2] Create user-friendly startup error handler in src/mythicmcp/server.py
- [ ] T009 [US2] Add configuration guidance message with environment variable examples in src/mythicmcp/server.py
- [ ] T010 [US2] Ensure ConfigurationError displays guidance instead of stack trace in src/mythicmcp/server.py
- [ ] T011 [US2] Add configuration section to README.md with environment variable documentation
- [ ] T012 [US2] Test unconfigured startup shows helpful message

**Checkpoint**: Users who run the tool without configuration see clear instructions

---

## Phase 5: User Story 3 - Use MythicMCP with AI Assistants (Priority: P3)

**Goal**: Provide MCP client configuration examples for popular AI assistants

**Independent Test**: Configure Claude Desktop with the provided JSON and verify MythicMCP tools are discovered

### Implementation for User Story 3

- [ ] T013 [P] [US3] Add Claude Desktop configuration example to README.md
- [ ] T014 [P] [US3] Add Cursor configuration example to README.md
- [ ] T015 [US3] Add available tools reference table to README.md
- [ ] T016 [US3] Add troubleshooting section to README.md with common issues and solutions
- [ ] T017 [US3] Test Claude Desktop integration with provided configuration

**Checkpoint**: Users can configure their AI assistant using provided examples

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation and validation

- [ ] T018 [P] Copy quickstart.md content to appropriate README.md sections
- [ ] T019 [P] Add badges to README.md (Python version, license, MCP version)
- [ ] T020 Verify all README.md links work correctly
- [ ] T021 Run end-to-end validation: fresh install → configure → connect client
- [ ] T022 Update CLAUDE.md with any new patterns or conventions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: SKIPPED - not needed for this feature
- **User Stories (Phase 3+)**: Can start immediately after Setup verification
  - User stories can proceed sequentially in priority order (P1 → P2 → P3)
  - US2 (configuration guidance) should complete before US3 (client examples) for better UX flow
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup - Independent, but logically follows US1
- **User Story 3 (P3)**: Can start after Setup - Builds on US1 and US2 for complete documentation flow

### Within Each User Story

- Documentation tasks can often run in parallel [P]
- Code changes should be sequential within a story
- Verification/testing tasks at the end of each story

### Parallel Opportunities

- T013 and T014 can run in parallel (different documentation sections)
- T018 and T019 can run in parallel (different README sections)
- User stories are primarily sequential due to documentation flow, but code tasks within US2 are independent

---

## Parallel Example: User Story 3

```bash
# Launch parallel documentation tasks:
Task: "Add Claude Desktop configuration example to README.md"
Task: "Add Cursor configuration example to README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup verification
2. Complete Phase 3: User Story 1 (installation instructions)
3. **STOP and VALIDATE**: Test `uv tool install .` works
4. Users can now install the tool!

### Incremental Delivery

1. Setup verification → Confirm infrastructure is correct
2. Add US1 → Users can install → **MVP Complete**
3. Add US2 → Users get configuration guidance → Better first-run experience
4. Add US3 → Users get client configuration examples → Complete documentation
5. Polish → Professional README with badges and cross-links

### Estimated Task Distribution

| Phase | Tasks | Focus |
|-------|-------|-------|
| Setup | 3 | Verification |
| US1 (P1) | 4 | Installation docs |
| US2 (P2) | 5 | Startup UX + config docs |
| US3 (P3) | 5 | Client configuration |
| Polish | 5 | Final validation |
| **Total** | **22** | |

---

## Notes

- This feature is primarily documentation and UX improvements
- Minimal code changes (startup error handling in server.py)
- Most tasks involve README.md updates
- quickstart.md already contains most content - tasks involve integrating it into README.md
- [P] tasks = different documentation sections, no conflicts
- Commit after each logical group of documentation updates
- Stop at any checkpoint to validate independently
