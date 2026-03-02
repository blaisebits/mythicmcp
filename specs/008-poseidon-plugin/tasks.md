# Tasks: Poseidon Agent Built-in Plugin

**Input**: Design documents from `/specs/008-poseidon-plugin/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit tests are requested (FR-008). Integration tests are config-only (FR-009).

**Organization**: Tasks grouped by user story. US1 and US2 are merged (both P1, same deliverable — the YAML file). US3 (plugin startup) is validated by unit tests. US4 (integration tests) is a separate phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: No project initialization needed — all infrastructure exists. This phase is a no-op.

*(No tasks — existing YAML loader, plugin system, and test framework are already in place.)*

---

## Phase 2: Foundational

**Purpose**: No foundational work needed — the YAML loader, executor, and plugin base classes are all reused as-is (FR-005).

*(No tasks — constraint is explicitly "no changes to the YAML loader.")*

---

## Phase 3: User Stories 1 & 2 — Full Poseidon Command Coverage (Priority: P1) 🎯 MVP

**Goal**: Create `poseidon.yaml` with all ~76 Poseidon 2.2.8 commands, covering every command category.

**Independent Test**: Load `poseidon.yaml` with `parse_yaml_config()` — it validates without errors and produces the expected tool count.

### Implementation

- [x] T001 [US1] Create `poseidon.yaml` agent header and metadata section in `src/mythicmcp/plugins/builtin/poseidon.yaml` — set name=poseidon, description, supported_os=[macOS, Linux], agent_version=2.2.8, mythic_version=3.3.0+
- [x] T002 [US1] Add Shell & Command Execution commands (shell, pty, run, jxa_macos, ssh) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — reference `refs/agents/poseidon/Payload_Type/poseidon/poseidon/agentfunctions/` for parameter details. Use `_macos` suffix and "(macOS only)" in description for jxa.
- [x] T003 [P] [US1] Add File Operations commands (ls, cat, cd, pwd, head, tail, mkdir, rm, cp, mv, download, upload, download_bulk, triagedirectory) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — flatten upload parameter groups per research R4.
- [x] T004 [P] [US1] Add Process Management commands (ps, kill, jobkill, jobs) to `src/mythicmcp/plugins/builtin/poseidon.yaml`
- [x] T005 [P] [US1] Add Environment Variable commands (getenv, setenv, unsetenv, curl_env_get, curl_env_set, curl_env_clear) to `src/mythicmcp/plugins/builtin/poseidon.yaml`
- [x] T006 [P] [US1] Add User & Credential commands (getuser, sudo, test_password, sshauth, prompt) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — flatten ssh parameter groups (password vs private_key).
- [x] T007 [P] [US1] Add Network Operations commands (ifconfig, portscan, curl, socks, rpfwd) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — use `choices` for curl method (GET/POST/PUT/DELETE), document array format for portscan hosts/ports.
- [x] T008 [P] [US1] Add Persistence commands (persist_launchd_macos, persist_loginitem_macos) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — use `_macos` suffix and "(macOS only)" in descriptions. Set `mythic_command` to the original name (e.g., `mythic_command: persist_launchd`).
- [x] T009 [P] [US1] Add Code Injection & Execution commands (libinject_macos, execute_library_macos, jsimport, jsimport_call) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — use `_macos` suffix for libinject and execute_library with `mythic_command` set to original names. Flatten execute_library parameter groups.
- [x] T010 [P] [US1] Add Logging & Data Collection commands (keylog, screencapture, clipboard, clipboard_monitor) to `src/mythicmcp/plugins/builtin/poseidon.yaml`
- [x] T011 [P] [US1] Add System Information commands (drives, lsopen, list_entitlements_macos, tcc_check_macos, keys, config, print_c2, print_p2p) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — use `_macos` suffix for list_entitlements and tcc_check with `mythic_command` set to original names.
- [x] T012 [P] [US1] Add Configuration & Control commands (sleep, update_c2, link_tcp, unlink_tcp, link_webshell, unlink_webshell, exit, caffeinate) to `src/mythicmcp/plugins/builtin/poseidon.yaml`
- [x] T013 [P] [US1] Add XPC commands (xpc_send_macos, xpc_service_macos, xpc_submit_macos, xpc_procinfo_macos, xpc_manageruid_macos, xpc_unload_macos, xpc_load_macos) to `src/mythicmcp/plugins/builtin/poseidon.yaml` — use `_macos` suffix on all with `mythic_command` set to original names (e.g., `mythic_command: xpc_send`).
- [x] T014 [P] [US1] Add Shell Config commands (shell_config, chmod) to `src/mythicmcp/plugins/builtin/poseidon.yaml`
- [x] T015 [US2] Review complete `poseidon.yaml` for consistency: verify all commands use consistent description style ("Execute X on a Poseidon callback"), parameter naming matches Apollo conventions where applicable, file_id params reference `core_upload_file`, macOS-only commands use `_macos` name suffix with correct `mythic_command` mapping to the original Poseidon command name, and all `mythic_command` values match actual Poseidon agent function names in `refs/agents/poseidon/`.

**Checkpoint**: `poseidon.yaml` is complete. Run `uv run pytest tests/unit/test_yaml_loader.py -v` — existing tests still pass (Poseidon loads but isn't yet asserted).

---

## Phase 4: User Story 3 — Plugin Loads at Startup (Priority: P2)

**Goal**: Verify the Poseidon plugin loads correctly via unit tests.

**Independent Test**: `uv run pytest tests/unit/test_yaml_loader.py -v -k poseidon` passes.

### Implementation

- [x] T016 [US3] Add `TestPoseidonYamlConfig` class to `tests/unit/test_yaml_loader.py` with tests: `test_poseidon_yaml_loads` (no validation errors), `test_poseidon_command_count` (assert >= 70), `test_poseidon_agent_metadata` (name, description, supported_os).
- [x] T017 [US3] Add spot-check tests to `tests/unit/test_yaml_loader.py`: verify shell command has `command` param (string, required), curl has `method` param with `choices` field, portscan has `hosts` param, upload has `file_id` and `remote_path` params, and a macOS-only command (e.g., `jxa_macos`) has `mythic_command` set to `jxa`.
- [x] T018 [US3] Run full unit test suite: `uv run pytest --ignore=tests/integration -x -q` — all tests pass including new Poseidon tests.

**Checkpoint**: All unit tests pass. Poseidon loads with correct metadata and expected tool count.

---

## Phase 5: User Story 4 — Integration Test Coverage (Priority: P3)

**Goal**: Add Poseidon test commands to the integration test sample config.

**Independent Test**: Config sample is valid YAML and includes a `poseidon:` section with representative commands.

### Implementation

- [x] T019 [US4] Add Poseidon agent definition to `tests/integration/config.sample.yaml` targets section — include a Linux target entry with poseidon agent reference.
- [x] T020 [US4] Add Poseidon test commands to `tests/integration/config.sample.yaml` under `test_commands.poseidon:` — include representative commands: shell (id), pwd, ls (/tmp), cat, ps, ifconfig, chmod, mkdir, upload, download, rm. Follow Apollo section style with category comments.

**Checkpoint**: Sample config is valid and includes Poseidon test commands.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation.

- [x] T021 [P] Update CLAUDE.md Available Plugins section to include Poseidon with tool count and description
- [x] T022 Run full unit test suite: `uv run pytest --ignore=tests/integration -x -q` — all tests pass
- [x] T023 Run quickstart.md validation — verify all steps are accurate for the final deliverable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No-op — skip
- **Foundational (Phase 2)**: No-op — skip
- **US1/US2 (Phase 3)**: Can start immediately — no prerequisites beyond existing codebase
- **US3 (Phase 4)**: Depends on Phase 3 (needs poseidon.yaml to test)
- **US4 (Phase 5)**: Independent of Phase 4 (config sample doesn't depend on unit tests)
- **Polish (Phase 6)**: Depends on Phases 3-5

### User Story Dependencies

- **US1/US2 (P1)**: No dependencies — create poseidon.yaml
- **US3 (P2)**: Depends on US1/US2 — needs poseidon.yaml to load in tests
- **US4 (P3)**: Can start after US1/US2 or in parallel with US3

### Within Phase 3 (poseidon.yaml authoring)

- T001 must complete first (agent header)
- T002-T014 can all run in parallel (independent command categories, same file but different sections)
- T015 must run last (review pass)

### Parallel Opportunities

- T003-T014 are all parallelizable (different command categories appended to same file)
- T016-T017 are sequential within Phase 4
- T019-T020 are sequential within Phase 5
- T021 can run in parallel with T022-T023

---

## Parallel Example: Phase 3

```bash
# After T001 (agent header), launch all command categories in parallel:
Task: "Add File Operations commands to poseidon.yaml"
Task: "Add Process Management commands to poseidon.yaml"
Task: "Add Environment Variable commands to poseidon.yaml"
Task: "Add Network Operations commands to poseidon.yaml"
Task: "Add XPC commands to poseidon.yaml"
# ... (all T003-T014 in parallel)
```

---

## Implementation Strategy

### MVP First (Phase 3 Only)

1. Create poseidon.yaml with all commands (T001-T015)
2. **STOP and VALIDATE**: Load with `parse_yaml_config()` — no errors
3. Run existing unit tests — nothing broken

### Incremental Delivery

1. Phase 3: poseidon.yaml → MVP complete
2. Phase 4: Unit tests → Validated
3. Phase 5: Integration config → Full coverage
4. Phase 6: Polish → Ship-ready

---

## Notes

- Total tasks: 23
- Tasks per user story: US1/US2=15, US3=3, US4=2, Polish=3
- Parallel opportunities: T003-T014 (12 tasks) in Phase 3; T021 in Phase 6
- MVP scope: Phase 3 only (poseidon.yaml)
- All tasks produce changes in exactly 4 files: poseidon.yaml (new), test_yaml_loader.py (modify), config.sample.yaml (modify), CLAUDE.md (modify)
- No Python code changes beyond test additions
- No YAML loader changes required
