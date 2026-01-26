# Tasks: Agent Plugin System

**Input**: Design documents from `/specs/003-agent-plugin-system/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create plugin system directory structure and base module scaffolding

- [X] T001 Create plugins directory structure at src/mythicmcp/plugins/
- [X] T002 Create builtin plugins directory at src/mythicmcp/plugins/builtin/
- [X] T003 [P] Create plugins package __init__.py at src/mythicmcp/plugins/__init__.py
- [X] T004 [P] Create builtin package __init__.py at src/mythicmcp/plugins/builtin/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core plugin infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement ToolDefinition dataclass in src/mythicmcp/plugins/base.py
- [X] T006 Implement AgentPlugin abstract base class in src/mythicmcp/plugins/base.py
- [X] T007 Implement LoadedPlugin and PluginLoadError dataclasses in src/mythicmcp/plugins/registry.py
- [X] T008 Implement PluginRegistry class with register_plugin, get_plugin, get_tool, get_all_tools, list_plugins methods in src/mythicmcp/plugins/registry.py
- [X] T009 Add TaskStatus enum to src/mythicmcp/models.py
- [X] T010 [P] Add ExecuteTaskRequest model to src/mythicmcp/models.py
- [X] T011 [P] Add TaskOutput model to src/mythicmcp/models.py
- [X] T012 [P] Add ExecuteTaskResponse model to src/mythicmcp/models.py
- [X] T013 [P] Add PluginToolSuccessResponse model to src/mythicmcp/models.py
- [X] T014 [P] Add PluginToolErrorResponse model to src/mythicmcp/models.py
- [X] T015 [P] Add AgentTypeMismatchError exception to src/mythicmcp/plugins/executor.py
- [X] T016 [P] Add CallbackAgentInfo model to src/mythicmcp/models.py
- [X] T017 Implement get_callback_agent_type helper function in src/mythicmcp/plugins/executor.py
- [X] T018 Implement validate_agent_type function in src/mythicmcp/plugins/executor.py
- [X] T019 Implement execute_task function using mythic.issue_task with timeout handling in src/mythicmcp/plugins/executor.py
- [X] T020 Implement get_task_output function using mythic.get_all_task_output_by_id in src/mythicmcp/plugins/executor.py

**Checkpoint**: Foundation ready - plugin base classes and task executor available

---

## Phase 3: User Story 1 - Load Agent-Specific Tools (Priority: P1) MVP

**Goal**: Enable MythicMCP to load agent plugins at startup and expose their tools via MCP protocol

**Independent Test**: Start MythicMCP with builtin plugins and verify apollo_* and arachne_* tools appear in tool list

### Implementation for User Story 1

- [X] T021 [US1] Implement discover_builtin_plugins function to scan plugins/builtin/ in src/mythicmcp/plugins/__init__.py
- [X] T022 [US1] Implement load_plugin function with error handling (logs warning, skips invalid) in src/mythicmcp/plugins/__init__.py
- [X] T023 [US1] Implement load_all_plugins function that populates registry in src/mythicmcp/plugins/__init__.py
- [X] T024 [US1] Implement generate_tool_function factory to create MCP-compatible async tool handlers in src/mythicmcp/plugins/__init__.py
- [X] T025 [US1] Implement register_plugin_tools function to register tools with FastMCP server in src/mythicmcp/plugins/__init__.py
- [X] T026 [US1] Add ListPluginsResponse model to src/mythicmcp/models.py
- [X] T027 [US1] Implement core_list_plugins tool in src/mythicmcp/server.py (FR-007)
- [X] T028 [US1] Modify server.py to call load_all_plugins and register_plugin_tools at startup
- [X] T029 [P] [US1] Create Apollo plugin skeleton with agent_name="apollo" in src/mythicmcp/plugins/builtin/apollo.py
- [X] T030 [P] [US1] Create Arachne plugin skeleton with agent_name="arachne" in src/mythicmcp/plugins/builtin/arachne.py
- [X] T031 [US1] Add apollo_shell tool definition with ApolloShellParams in src/mythicmcp/plugins/builtin/apollo.py
- [X] T032 [US1] Add arachne_shell tool definition with ArachneShellParams in src/mythicmcp/plugins/builtin/arachne.py
- [X] T033 [US1] Verify plugin loading logs success/warnings at appropriate log levels

**Checkpoint**: User Story 1 complete - plugins load at startup, tools appear in MCP tool list

---

## Phase 4: User Story 2 - Execute Agent Commands on Callbacks (Priority: P2)

**Goal**: Enable execution of plugin tools against callbacks with agent type validation and result retrieval

**Independent Test**: Call apollo_shell on an Apollo callback and verify task creation + output return; call apollo_shell on Arachne callback and verify agent_mismatch error

### Implementation for User Story 2

- [X] T034 [US2] Implement _execute_with_validation helper in src/mythicmcp/plugins/executor.py (validates agent type, executes task, gets output)
- [X] T035 [US2] Implement apollo_shell handler using execute_task in src/mythicmcp/plugins/builtin/apollo.py
- [X] T036 [US2] Implement arachne_shell handler using execute_task in src/mythicmcp/plugins/builtin/arachne.py
- [X] T037 [P] [US2] Add apollo_pwd tool (simple command, no params beyond callback_id) in src/mythicmcp/plugins/builtin/apollo.py
- [X] T038 [P] [US2] Add apollo_ls tool with optional path param in src/mythicmcp/plugins/builtin/apollo.py
- [X] T039 [P] [US2] Add apollo_cd tool with path param in src/mythicmcp/plugins/builtin/apollo.py
- [X] T040 [P] [US2] Add apollo_cat tool with path param in src/mythicmcp/plugins/builtin/apollo.py
- [X] T041 [P] [US2] Add apollo_ps tool in src/mythicmcp/plugins/builtin/apollo.py
- [X] T042 [P] [US2] Add apollo_run tool with executable and arguments params in src/mythicmcp/plugins/builtin/apollo.py
- [X] T043 [P] [US2] Add apollo_download tool with path param in src/mythicmcp/plugins/builtin/apollo.py
- [X] T044 [P] [US2] Add apollo_execute_assembly tool with assembly_name and assembly_arguments params in src/mythicmcp/plugins/builtin/apollo.py
- [X] T045 [P] [US2] Add apollo_screenshot tool in src/mythicmcp/plugins/builtin/apollo.py
- [X] T046 [P] [US2] Add arachne_pwd tool in src/mythicmcp/plugins/builtin/arachne.py
- [X] T047 [P] [US2] Add arachne_ls tool with optional path param in src/mythicmcp/plugins/builtin/arachne.py
- [X] T048 [P] [US2] Add arachne_cd tool with path param in src/mythicmcp/plugins/builtin/arachne.py
- [X] T049 [P] [US2] Add arachne_rm tool with path param in src/mythicmcp/plugins/builtin/arachne.py
- [X] T050 [P] [US2] Add arachne_download tool with path param in src/mythicmcp/plugins/builtin/arachne.py
- [X] T051 [P] [US2] Add arachne_upload tool with remote_path and file_contents params in src/mythicmcp/plugins/builtin/arachne.py
- [X] T052 [P] [US2] Add arachne_execute_assembly tool in src/mythicmcp/plugins/builtin/arachne.py
- [X] T053 [US2] Implement timeout error handling and partial result return in src/mythicmcp/plugins/executor.py

**Checkpoint**: User Story 2 complete - all 18 plugin tools execute commands and return results

---

## Phase 5: User Story 3 - Install New Agent Plugins (Priority: P3)

**Goal**: Enable discovery and loading of additional plugins beyond builtins

**Independent Test**: Add a minimal test plugin file, restart MythicMCP, verify new agent tools appear

### Implementation for User Story 3

- [X] T054 [US3] Add MYTHICMCP_PLUGINS_DIR config option in src/mythicmcp/config.py
- [X] T055 [US3] Implement discover_external_plugins to scan configured plugins directory in src/mythicmcp/plugins/__init__.py
- [X] T056 [US3] Update load_all_plugins to include external plugins in src/mythicmcp/plugins/__init__.py
- [X] T057 [US3] Implement plugin name collision detection (log warning if agent_name already registered) in src/mythicmcp/plugins/registry.py
- [X] T058 [US3] Add plugin load errors to core_list_plugins response in src/mythicmcp/server.py
- [X] T059 [US3] Verify system functions normally with no plugins (only core tools available)

**Checkpoint**: User Story 3 complete - external plugins can be added without code changes

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [X] T060 [P] Add docstrings to all public functions in src/mythicmcp/plugins/
- [X] T061 [P] Add type hints to all function signatures in src/mythicmcp/plugins/
- [X] T062 [P] Add logging for plugin operations (load, register, execute) at appropriate levels
- [ ] T063 Run quickstart.md validation scenarios manually (requires live Mythic instance)
- [X] T064 Verify all 18 plugin tools match contracts/mcp-tools.md specifications

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs plugin loading to work)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (extends plugin discovery)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Requires US1 (plugins must load before tools can execute)
- **User Story 3 (P3)**: Requires US1 (extends existing loading mechanism)

### Within Each Phase

- T005-T006 (base.py) must complete before T007-T008 (registry.py)
- T017-T020 (executor.py) can run in parallel with T009-T016 (models.py)
- T021-T028 must be sequential (build plugin loading pipeline)
- T029-T030 (plugin skeletons) can run in parallel
- T034 (validation helper) must complete before T035-T052 (tool implementations)
- T037-T052 can all run in parallel (different tool implementations)

### Parallel Opportunities

**Phase 1**:
```
T003, T004 can run in parallel
```

**Phase 2**:
```
T010, T011, T012, T013, T014, T015, T016 can all run in parallel
```

**Phase 3**:
```
T029, T030 can run in parallel (plugin skeletons)
```

**Phase 4**:
```
T037, T038, T039, T040, T041, T042, T043, T044, T045 (Apollo tools) can run in parallel
T046, T047, T048, T049, T050, T051, T052 (Arachne tools) can run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (16 tasks)
3. Complete Phase 3: User Story 1 (13 tasks)
4. **STOP and VALIDATE**: Verify plugins load and tools appear in MCP
5. Can deploy with tool loading only (no execution yet)

### Incremental Delivery

1. Setup + Foundational + US1 → Plugin loading works (MVP!)
2. Add US2 → Commands execute on callbacks (full functionality)
3. Add US3 → External plugin support (extensibility)
4. Each increment adds value without breaking previous functionality

### Suggested MVP Scope

**User Story 1 only** - Total: 33 tasks (Phases 1-3)

This delivers:
- Plugin system infrastructure
- Builtin Apollo and Arachne plugins
- Tools visible in MCP tool list
- core_list_plugins management tool

Operators can see available agent tools even before execution is implemented.

---

## Notes

- All tool implementations follow the same pattern: Pydantic params model → handler → execute_task
- Constitution compliance verified in plan.md (all 5 principles pass)
- 18 total plugin tools: 10 Apollo + 8 Arachne (meets SC-003: at least 10 commands each)
- Timeout handling uses dual-layer: asyncio.timeout + Mythic's native timeout
