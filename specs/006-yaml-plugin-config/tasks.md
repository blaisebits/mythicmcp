# Tasks: YAML-Driven Agent Plugin Configuration

**Input**: Design documents from `/specs/006-yaml-plugin-config/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Add PyYAML to main dependencies

- [ ] T001 Move pyyaml from dev to main dependencies in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic config validation models and YAML loading infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Create Pydantic config models (ParameterConfigModel, CommandConfigModel, AgentConfigModel) in src/mythicmcp/plugins/yaml_loader.py with all validation rules from data-model.md: parameter types (string/integer/boolean), role (task/meta), name constraints (Python identifier, not callback_id/timeout), type-specific constraints (min/max for integer, choices for string), default-type matching, command name uniqueness, agent name format (lowercase alphanumeric + hyphens, 1-50 chars), supported_os validation (Windows/Linux/macOS), timeout range (30-300)
- [ ] T003 Implement YAML file parsing function in src/mythicmcp/plugins/yaml_loader.py that reads a YAML file with yaml.safe_load(), validates against AgentConfigModel, and returns the validated config or a structured error with file path, agent name (if parseable), and per-field error messages matching the validation error contract
- [ ] T004 Implement dynamic Pydantic parameter model builder in src/mythicmcp/plugins/yaml_loader.py that takes a CommandConfigModel and generates a Pydantic BaseModel class with: implicit callback_id (int, required) field, implicit timeout (int, optional with command default, ge=30 le=300) field, all declared parameters mapped to their Python types with Field() constraints (description, default, ge/le for integers), preserving field ordering as callback_id first then declared params then timeout last
- [ ] T005 Implement handler generator function in src/mythicmcp/plugins/yaml_loader.py that takes an AgentConfigModel and a CommandConfigModel, and returns an async handler function that: extracts callback_id and timeout from params, collects all task-role parameters into a dict, calls execute_with_validation(ctx, callback_id, agent_name, mythic_command, params_dict, timeout), and returns the result
- [ ] T006 Implement YAML-to-AgentPlugin adapter in src/mythicmcp/plugins/yaml_loader.py: a class or function that takes a validated AgentConfigModel and produces an AgentPlugin instance with get_tools() returning ToolDefinition list built from the generated parameter models and handler functions (from T004 and T005)

**Checkpoint**: YAML loading infrastructure complete — config files can be parsed, validated, and converted to AgentPlugin instances

---

## Phase 3: User Story 1 - Define Agent Commands via Configuration File (Priority: P1) MVP

**Goal**: YAML config files are discovered, loaded, validated, and registered as MCP tools at startup

**Independent Test**: Create apollo.yaml, start server, verify all 10 tools appear with correct parameter schemas

### Implementation for User Story 1

- [ ] T007 [US1] Create Apollo YAML configuration file at src/mythicmcp/plugins/builtin/apollo.yaml with all 10 commands matching current apollo.py exactly: shell (command:str required, timeout default 60), pwd (timeout default 60), ls (path:str default ".", timeout default 60), cd (path:str required, timeout default 60), cat (path:str required, timeout default 60), ps (timeout default 60), run (executable:str required, arguments:str default "", timeout default 60), download (path:str required, timeout default 120), execute_assembly (assembly_name:str required, assembly_arguments:str default "", timeout default 120), screenshot (timeout default 120)
- [ ] T008 [US1] Implement YAML config discovery function in src/mythicmcp/plugins/yaml_loader.py that finds .yaml and .yml files in a given directory (used for both the builtin plugins directory and the external plugins directory), skipping files starting with _ or ., and returns list of file paths
- [ ] T009 [US1] Add YAML plugin loading to load_all_plugins() in src/mythicmcp/plugins/__init__.py: discover YAML files in builtin directory, parse and validate each via yaml_loader, convert to AgentPlugin, register in PluginRegistry. Load YAML configs before Python modules. If YAML and Python define the same agent name, skip the Python module with a warning log. Also discover YAML files in external plugins directory (MYTHICMCP_PLUGINS_DIR) if set.
- [ ] T010 [US1] Delete src/mythicmcp/plugins/builtin/apollo.py and remove "mythicmcp.plugins.builtin.apollo" from the hardcoded builtin modules list in load_all_plugins()

**Checkpoint**: Apollo is fully config-driven. Server starts with all 10 apollo_* tools registered from apollo.yaml.

---

## Phase 4: User Story 2 - Maintain Backward Compatibility (Priority: P1)

**Goal**: Config-driven Apollo tools produce identical MCP tool schemas and execution behavior as the previous code-based implementation

**Independent Test**: Run existing unit tests and integration tests — all must pass without modification

### Verification Checkpoints for User Story 2

> **NOTE**: These are verification tasks, not implementation tasks. If any check fails, fix the issue in apollo.yaml or yaml_loader.py before proceeding.

- [ ] T011 [US2] Verify generated tool names match exactly: apollo_shell, apollo_pwd, apollo_ls, apollo_cd, apollo_cat, apollo_ps, apollo_run, apollo_download, apollo_execute_assembly, apollo_screenshot by running existing tests/unit/test_plugin_tools.py
- [ ] T012 [US2] Verify generated tool descriptions match current descriptions exactly by comparing apollo.yaml descriptions against the values previously in apollo.py
- [ ] T013 [US2] Verify generated parameter schemas match: each tool's kwargs annotation must have identical field names, types, required/optional status, defaults, and constraints (ge/le) as the previous Pydantic model classes
- [ ] T014 [US2] Run existing integration tests (if Mythic server available) to verify end-to-end command execution produces identical PluginToolSuccessResponse/PluginToolErrorResponse results
- [ ] T015 [US2] Verify core_list_plugins output includes Apollo with correct agent_name, description, tool_count=10, and supported_os=["Windows"]
- [ ] T015a [US2] Run integration test (if Mythic server available) issuing a command that does not exist on the Apollo agent to verify the system returns an appropriate Mythic API error to the operator

**Checkpoint**: All existing tests pass. Tool schemas are byte-identical to previous implementation.

---

## Phase 5: User Story 3 - Validate Configuration Files at Startup (Priority: P2)

**Goal**: Invalid YAML configs produce clear, actionable error messages and are skipped without crashing the server

**Independent Test**: Create invalid config files and verify specific error messages

### Implementation for User Story 3

- [ ] T016 [US3] Add unit tests in tests/unit/test_yaml_loader.py for missing required fields: config missing agent.name, missing agent.description, missing agent.supported_os, missing commands, command missing name, command missing description, parameter missing name, parameter missing type, parameter missing description
- [ ] T017 [US3] Add unit tests in tests/unit/test_yaml_loader.py for invalid field values: unsupported parameter type (e.g., "float"), invalid agent name format (uppercase, special chars, too long), invalid supported_os value (e.g., "FreeBSD"), timeout out of range (<30 or >300), duplicate command names within agent, parameter name conflicts (callback_id, timeout, ctx, context, self), min > max, default value type mismatch, choices on integer param, min/max on string param
- [ ] T018 [US3] Add unit tests in tests/unit/test_yaml_loader.py for YAML parse errors: malformed YAML syntax, empty file, file with only comments, non-dict top-level structure
- [ ] T019 [US3] Add unit test in tests/unit/test_yaml_loader.py verifying that unrecognized top-level keys in the YAML produce a warning log but still load successfully
- [ ] T020 [US3] Verify that validation errors include the file path and specific field path (e.g., "commands[0].parameters[1].type") in the error message
- [ ] T020a [US3] Add unit test in tests/unit/test_yaml_loader.py verifying that two YAML config files defining the same agent name both fail to load, with an error identifying the conflicting files and agent name

**Checkpoint**: All validation edge cases have test coverage. Invalid configs produce clear errors.

---

## Phase 6: User Story 4 - Add a New Agent Plugin Without Writing Code (Priority: P2)

**Goal**: A new agent can be defined purely via YAML config with zero Python code

**Independent Test**: Create a minimal testagent.yaml, start server, verify testagent_ping tool appears

### Implementation for User Story 4

- [ ] T021 [US4] Add unit test in tests/unit/test_yaml_loader.py that creates a minimal agent YAML config (1 command, 1 parameter) and verifies it produces a valid AgentPlugin with correct metadata and one ToolDefinition
- [ ] T022 [US4] Add unit test in tests/unit/test_yaml_loader.py that creates a 3-command agent YAML config with mixed parameter types (string, integer, boolean) and verifies all 3 tools are generated with correct schemas
- [ ] T023 [US4] Add unit test verifying external plugin directory YAML discovery works: set MYTHICMCP_PLUGINS_DIR to a temp directory containing a YAML config and verify the plugin is loaded
- [ ] T024 [US4] Verify that config-driven plugins coexist with code-based plugins (Arachne) by loading both and confirming all tools from both appear in the registry without conflicts

**Checkpoint**: New agents can be created via config only. External directory loading works.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [ ] T025 Update CLAUDE.md with 006-yaml-plugin-config summary: YAML plugin config system, apollo.yaml replaces apollo.py, new yaml_loader.py module, pyyaml added to main dependencies
- [ ] T026 Update Plugin System section in CLAUDE.md to document YAML config approach alongside code-based plugins, including example YAML snippet
- [ ] T027 Run full unit test suite (uv run pytest tests/unit/ -v) and verify all tests pass
- [ ] T028 Run quickstart.md validation scenarios: create a new agent config, verify tool registration, verify parameter validation, verify error handling

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs Apollo migrated to verify compat)
- **User Story 3 (Phase 5)**: Depends on Foundational phase only (validation tests don't need Apollo migration)
- **User Story 4 (Phase 6)**: Depends on Foundational phase only (new agent tests don't need Apollo migration)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 2 complete. Creates apollo.yaml and wires YAML loading into __init__.py
- **User Story 2 (P1)**: Requires User Story 1 complete (Apollo must be migrated to verify backward compat)
- **User Story 3 (P2)**: Can start after Phase 2 (tests validation logic directly, independent of Apollo migration)
- **User Story 4 (P2)**: Can start after Phase 2 (tests new agent creation, independent of Apollo migration)

### Within Each User Story

- Config models before loading functions
- Loading functions before registration integration
- Core implementation before verification

### Parallel Opportunities

- T016, T017, T018, T019 (US3 validation tests) can all run in parallel
- T021, T022, T023 (US4 tests) can all run in parallel
- US3 and US4 can be worked on in parallel after Phase 2
- T025 and T026 (docs) can run in parallel

---

## Parallel Example: User Story 3

```bash
# Launch all validation test tasks together:
Task: "Unit tests for missing required fields in tests/unit/test_yaml_loader.py"
Task: "Unit tests for invalid field values in tests/unit/test_yaml_loader.py"
Task: "Unit tests for YAML parse errors in tests/unit/test_yaml_loader.py"
Task: "Unit test for unrecognized keys warning in tests/unit/test_yaml_loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add pyyaml dependency)
2. Complete Phase 2: Foundational (config models, parser, model builder, handler generator, adapter)
3. Complete Phase 3: User Story 1 (apollo.yaml, discovery, loader integration, delete apollo.py)
4. **STOP and VALIDATE**: Start server, verify 10 Apollo tools work
5. Proceed to backward compat verification (US2)

### Incremental Delivery

1. Setup + Foundational → YAML infrastructure ready
2. User Story 1 → Apollo migrated to YAML → Deploy/Demo (MVP!)
3. User Story 2 → Backward compat verified → Confidence gate
4. User Story 3 + 4 (parallel) → Validation + new agent support
5. Polish → Docs and final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The executor.py, registry.py, base.py, server.py, and models.py files are NOT modified in this feature
