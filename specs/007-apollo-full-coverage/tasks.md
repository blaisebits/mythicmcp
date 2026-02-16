# Tasks: Apollo Full Command Coverage

**Input**: Design documents from `/specs/007-apollo-full-coverage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test updates included only where existing assertions must change.

**Organization**: Tasks grouped by user story (US1: Full Command Access, US2: Version Tracking Metadata).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No project initialization needed — existing codebase. This phase captures prerequisite research.

- [x] T001 Audit all 62 Apollo commands from refs/agents/Apollo/Payload_Type/apollo/apollo/mythic/agent_functions/ and produce a verified command-parameter manifest to use as source of truth for YAML authoring

**Checkpoint**: Command manifest verified, ready to author YAML entries.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema change that must land before new commands can use metadata.

**⚠️ CRITICAL**: Metadata field must be added before apollo.yaml gains a `metadata` section.

- [x] T002 Add optional `metadata: dict[str, Any] | None = None` field to `YamlConfigModel` in src/mythicmcp/plugins/yaml_loader.py
- [x] T003 Update `warn_extra_fields` validator in src/mythicmcp/plugins/yaml_loader.py to confirm `metadata` no longer appears in `model_extra` (no code change needed if field is declared — verify with a test)
- [x] T004 [P] Add unit test for metadata field parsing in tests/unit/test_yaml_loader.py — verify YAML with `metadata:` section loads without warnings
- [x] T005 [P] Add unit test for metadata field absence in tests/unit/test_yaml_loader.py — verify YAML without `metadata:` still loads (backward compat)

**Checkpoint**: YamlConfigModel accepts `metadata` without warnings. All existing tests pass.

---

## Phase 3: User Story 1 — Full Apollo Command Access (Priority: P1) 🎯 MVP

**Goal**: Expand apollo.yaml from 10 to 62 commands covering 100% of Apollo 2.4.8.

**Independent Test**: Load apollo.yaml, verify 62 tools registered with correct parameter schemas.

### Implementation for User Story 1

Commands are grouped by category. Tasks within a category are parallelizable since they edit the same file but append independent blocks. In practice, execute sequentially within the file but the grouping shows logical independence.

- [x] T006 [US1] Add `metadata` section to top of src/mythicmcp/plugins/builtin/apollo.yaml with `agent_version: "2.4.8"` and `mythic_version: "3.4.6+"`
- [x] T007 [US1] Update existing `ls` command in src/mythicmcp/plugins/builtin/apollo.yaml to add optional `host` parameter (string, not required)
- [x] T008 [US1] Update existing `download` command in src/mythicmcp/plugins/builtin/apollo.yaml to add optional `host` parameter and rename `path` param to `file` to match reference
- [x] T009 [US1] Add shell/command execution commands to src/mythicmcp/plugins/builtin/apollo.yaml: `powershell`, `powerpick`, `powershell_import`, `wmiexecute` (4 commands)
- [x] T010 [US1] Add file operation commands to src/mythicmcp/plugins/builtin/apollo.yaml: `upload`, `cp`, `mv`, `rm`, `mkdir` (5 commands)
- [x] T011 [US1] Add process management commands to src/mythicmcp/plugins/builtin/apollo.yaml: `kill`, `jobs`, `jobkill` (3 commands)
- [x] T012 [US1] Add agent management commands to src/mythicmcp/plugins/builtin/apollo.yaml: `sleep`, `exit`, `load` (3 commands)
- [x] T013 [US1] Add assembly/code execution commands to src/mythicmcp/plugins/builtin/apollo.yaml: `inline_assembly`, `assembly_inject`, `register_assembly`, `register_file`, `register_coff`, `execute_pe`, `execute_coff` (7 commands)
- [x] T014 [US1] Add injection/spawning commands to src/mythicmcp/plugins/builtin/apollo.yaml: `inject`, `shinject`, `psinject`, `spawn`, `screenshot_inject`, `keylog_inject` (6 commands)
- [x] T015 [US1] Add token/identity commands to src/mythicmcp/plugins/builtin/apollo.yaml: `make_token`, `steal_token`, `rev2self`, `getprivs`, `whoami`, `getsystem` (6 commands)
- [x] T016 [US1] Add credential operation commands to src/mythicmcp/plugins/builtin/apollo.yaml: `mimikatz`, `dcsync`, `pth`, `printspoofer` (4 commands)
- [x] T017 [US1] Add network reconnaissance commands to src/mythicmcp/plugins/builtin/apollo.yaml: `ifconfig`, `netstat`, `listpipes`, `net_shares`, `net_dclist`, `net_localgroup`, `net_localgroup_member`, `ldap_query` (8 commands)
- [x] T018 [US1] Add registry commands to src/mythicmcp/plugins/builtin/apollo.yaml: `reg_query`, `reg_write_value` (2 commands)
- [x] T019 [US1] Add service control command to src/mythicmcp/plugins/builtin/apollo.yaml: `sc` with flattened parameter group (action + all optional params) (1 command)
- [x] T020 [US1] Add kerberos ticket commands to src/mythicmcp/plugins/builtin/apollo.yaml: `ticket_store_add`, `ticket_store_list`, `ticket_store_purge`, `ticket_cache_add`, `ticket_cache_list`, `ticket_cache_purge`, `ticket_cache_extract` (7 commands)
- [x] T021 [US1] Add process/injection config commands to src/mythicmcp/plugins/builtin/apollo.yaml: `spawnto_x64`, `spawnto_x86`, `ppid`, `blockdlls`, `get_injection_techniques`, `set_injection_technique` (6 commands)
- [x] T022 [US1] Add P2P/networking commands to src/mythicmcp/plugins/builtin/apollo.yaml: `link`, `unlink`, `socks`, `rpfwd` (4 commands)
- [x] T023 [US1] Add lateral movement commands to src/mythicmcp/plugins/builtin/apollo.yaml: `jump_wmi`, `jump_psexec` (2 commands)
- [x] T024 [US1] Validate apollo.yaml loads without errors — run `load_yaml_plugin()` on the file and verify 62 tools returned
- [x] T025 [US1] Update `test_apollo_yaml_loads` in tests/unit/test_yaml_loader.py to assert `len(result.get_tools()) == 62`
- [x] T026 [US1] Update `test_apollo_tool_names` in tests/unit/test_yaml_loader.py to assert the full sorted list of 62 command names
- [x] T027 [US1] Update `test_builtin_yaml_plugins_load` in tests/unit/test_yaml_loader.py to assert `len(apollo_tools) == 62`

**Checkpoint**: Apollo plugin registers 62 tools. All tests pass.

---

## Phase 4: User Story 2 — Version Tracking Metadata (Priority: P2)

**Goal**: Metadata section present in apollo.yaml and parseable without warnings.

**Independent Test**: Load apollo.yaml, verify metadata.agent_version is accessible and no warnings emitted.

### Implementation for User Story 2

- [x] T028 [US2] Add unit test in tests/unit/test_yaml_loader.py verifying `metadata` dict is accessible on loaded `YamlConfigModel` from apollo.yaml and contains `agent_version` key
- [x] T029 [US2] Optionally add `metadata` section to src/mythicmcp/plugins/builtin/arachne.yaml with `agent_version` for consistency

**Checkpoint**: Metadata tests pass. Both builtin plugins have version tracking.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all changes.

- [x] T030 Run full test suite (`uv run pytest tests/ -v`) and verify all tests pass
- [x] T031 Update CLAUDE.md to reflect new Apollo tool count (10 → 62) in Available Plugins section
- [x] T032 Verify no "unrecognized key" warnings in test output for metadata field

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — research/audit only
- **Foundational (Phase 2)**: Depends on T001 completion — adds metadata field to schema
- **User Story 1 (Phase 3)**: Depends on Phase 2 (metadata field must exist for T006)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (apollo.yaml must have metadata to test)
- **Polish (Phase 5)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational only. No dependency on US2.
- **User Story 2 (P2)**: Depends on US1 (tests verify metadata in the completed apollo.yaml). Could run in parallel if metadata tests use a standalone fixture instead.

### Within User Story 1

- T006 (metadata section) should be first
- T007-T008 (update existing commands) before adding new ones
- T009-T023 (new commands by category) are logically independent but edit the same file — execute sequentially
- T024 (validation) after all commands added
- T025-T027 (test updates) after T024 confirms correctness

### Parallel Opportunities

- T004 and T005 (metadata tests) can run in parallel
- T025, T026, T027 (test updates) can be done as a single edit session
- T028 and T029 (US2 tasks) can run in parallel

---

## Parallel Example: Phase 2

```bash
# Foundation metadata tests can run in parallel:
Task: "Add unit test for metadata field parsing in tests/unit/test_yaml_loader.py"
Task: "Add unit test for metadata field absence in tests/unit/test_yaml_loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Audit command manifest (T001)
2. Complete Phase 2: Add metadata field to YamlConfigModel (T002-T005)
3. Complete Phase 3: Add all 52 new commands + metadata to apollo.yaml (T006-T027)
4. **STOP and VALIDATE**: Run `uv run pytest tests/ -v` — all 152+ tests pass, Apollo reports 62 tools
5. Ready for review

### Incremental Delivery

1. Foundation → metadata schema ready
2. US1 → 62 Apollo commands → full operator coverage (MVP!)
3. US2 → metadata tests + arachne.yaml consistency → maintainability
4. Polish → docs, final validation

---

## Notes

- The bulk of work is YAML authoring (T009-T023) — 52 command entries with parameters from the research audit
- Only 1 line of Python changes (T002) — adding `metadata` field to YamlConfigModel
- Test changes are assertion updates (tool counts) + 2-3 new metadata tests
- File parameters use `file_id` from `core_upload_file` — document in parameter descriptions
- Parameter groups (sc, pth, make_token, shinject) are flattened per Research §R7
- Raw command-line commands (net_dclist, net_localgroup, set_injection_technique, printspoofer) get a single string parameter per Research §R6
