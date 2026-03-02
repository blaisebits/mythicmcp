# Tasks: Arachne Full Command Coverage

**Input**: Design documents from `/specs/009-arachne-full-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Unit test validation included in polish phase to confirm YAML loads correctly.

**Organization**: Tasks grouped by user story. All tasks modify a single file (`src/mythicmcp/plugins/builtin/arachne.yaml`) so parallelism is limited, but stories are logically independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - Fix Upload and Execute Assembly Parameters (Priority: P1) 🎯 MVP

**Goal**: Make `upload` and `execute_assembly` commands functional by correcting parameter names and types to match Mythic agent source.

**Independent Test**: Call `arachne_upload` with a file_id and remote_path, and `arachne_execute_assembly` with a file_id and arguments against a live Arachne callback.

### Implementation for User Story 1

- [x] T001 [US1] Replace `upload` command parameters in `src/mythicmcp/plugins/builtin/arachne.yaml`: change `file_contents` param to `file` (type: string, description: "file_id from core_upload_file for the file to upload", required: true); update command description to include "Use file_id from core_upload_file for the file parameter." per contract in `specs/009-arachne-full-coverage/contracts/yaml-parameter-schema.md`
- [x] T002 [US1] Replace `execute_assembly` command parameters in `src/mythicmcp/plugins/builtin/arachne.yaml`: change `assembly_name` param to `file` (type: string, description: "file_id from core_upload_file containing the .NET assembly", required: true); change `assembly_arguments` param to `arguments` (type: string, description: "Arguments to pass to assembly", default: "") per contract

**Checkpoint**: Upload and execute_assembly parameters now match Mythic agent source. YAML should still load without errors.

---

## Phase 2: User Story 2 - Fix Download Parameter Name (Priority: P1)

**Goal**: Make `download` command functional by renaming parameter from `path` to `file_path`.

**Independent Test**: Call `arachne_download` with a `file_path` argument against a live Arachne callback.

### Implementation for User Story 2

- [x] T003 [US2] Rename `download` command parameter in `src/mythicmcp/plugins/builtin/arachne.yaml`: change param name from `path` to `file_path`; update description to "Path to file to download" per contract

**Checkpoint**: Download parameter name matches Mythic agent source.

---

## Phase 3: User Story 3 - Correct Platform Restrictions (Priority: P2)

**Goal**: Update `cd` and `execute_assembly` descriptions to reflect Windows-only platform restrictions.

**Independent Test**: Inspect command descriptions in loaded plugin and confirm platform notes are present.

### Implementation for User Story 3

- [x] T004 [US3] Update `cd` command description in `src/mythicmcp/plugins/builtin/arachne.yaml`: change to "Change working directory on an Arachne webshell (Windows only)" per contract
- [x] T005 [US3] Update `execute_assembly` command description in `src/mythicmcp/plugins/builtin/arachne.yaml`: ensure it reads "Execute a .NET assembly on an Arachne ASPX webshell (Windows/ASPX only). Use file_id from core_upload_file for the file parameter." (may already be set by T002; verify and adjust if needed)

**Checkpoint**: Platform restrictions clearly noted in command descriptions.

---

## Phase 4: User Story 4 - Add Agent Version Metadata (Priority: P3)

**Goal**: Add metadata section with agent version for traceability, matching Apollo 007 pattern.

**Independent Test**: Confirm YAML loads successfully with metadata section; verify `agent_version: "0.0.4"` is present.

### Implementation for User Story 4

- [x] T006 [US4] Add `metadata` section with `agent_version: "0.0.4"` to `src/mythicmcp/plugins/builtin/arachne.yaml` between the `agent` block and `commands` block, per contract

**Checkpoint**: Metadata present and YAML loads correctly.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate all changes work together and update related test configuration.

- [x] T007 Run existing unit tests to confirm updated YAML loads without errors: `pytest tests/unit/test_yaml_loader.py -v`
- [x] T008 Update integration test config in `tests/integration/config.arachne.yaml` to use corrected parameter names (`file_path` for download, `file` for upload/execute_assembly, `arguments` for execute_assembly)
- [x] T009 Run quickstart.md validation: start MCP server and confirm Arachne plugin loads with 8 commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US2)**: No dependencies — can start immediately (different command section in same file)
- **Phase 3 (US3)**: T005 depends on T002 (execute_assembly description set in US1)
- **Phase 4 (US4)**: No dependencies — can start immediately
- **Phase 5 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Independent — modifies upload + execute_assembly sections
- **US2 (P1)**: Independent — modifies download section only
- **US3 (P2)**: T005 may overlap with T002 on execute_assembly description; execute T002 first
- **US4 (P3)**: Independent — adds new metadata section

### Parallel Opportunities

- T001 and T002 modify different commands within US1 but same file — execute sequentially
- US1, US2, and US4 modify different sections of the same file — can be combined into a single editing pass
- T007 and T008 modify different files and can run in parallel

---

## Parallel Example: Polish Phase

```bash
# After all user stories complete, run in parallel:
Task: "Run unit tests: pytest tests/unit/test_yaml_loader.py -v"
Task: "Update integration config in tests/integration/config.arachne.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Fix upload + execute_assembly (T001, T002)
2. **STOP and VALIDATE**: Run unit tests to confirm YAML loads
3. The two most critical broken commands are now fixed

### Incremental Delivery

1. Fix upload + execute_assembly (US1) → validate
2. Fix download (US2) → validate — all 3 broken commands now fixed
3. Correct platform descriptions (US3) → validate
4. Add metadata (US4) → validate
5. Polish: update test config, run full validation

### Single-Pass Strategy (Recommended)

Given all changes are to one YAML file, the most efficient approach is:

1. Apply all YAML edits (T001–T006) in a single editing pass
2. Run unit tests (T007)
3. Update integration config (T008)
4. Validate server startup (T009)

---

## Notes

- All 6 implementation tasks (T001–T006) modify `src/mythicmcp/plugins/builtin/arachne.yaml`
- No Python code changes required — YAML loader and executor already support the corrected patterns
- Reference contracts in `specs/009-arachne-full-coverage/contracts/yaml-parameter-schema.md` for exact YAML syntax
- Reference Arachne agent source in `refs/agents/arachne/Payload_Type/arachne/arachne/agent_functions/` for parameter verification
