# Feature Specification: Agent Plugin System

**Feature Branch**: `003-agent-plugin-system`
**Created**: 2026-01-25
**Status**: Draft
**Input**: User description: "create a plugin system that will allow adding additional tools for agents like arachne and apollo"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load Agent-Specific Tools (Priority: P1) 🎯 MVP

A security operator using MythicMCP wants to access agent-specific commands (like Apollo's `execute_assembly` or Arachne's `shell`) through their AI assistant. When MythicMCP starts with agent plugins installed, those agents' tools should automatically become available.

**Why this priority**: This is the core value proposition - without agent-specific tools, operators are limited to only the 4 core tools and cannot perform meaningful post-exploitation tasks.

**Independent Test**: Can be fully tested by installing a plugin and verifying its tools appear in the MCP tool list.

**Acceptance Scenarios**:

1. **Given** MythicMCP is running with the Apollo plugin installed, **When** the operator lists available tools, **Then** Apollo-specific tools (e.g., `apollo_execute_assembly`, `apollo_shell`) appear alongside core tools
2. **Given** MythicMCP has multiple agent plugins installed, **When** the operator lists available tools, **Then** tools from all installed plugins are available with clear agent prefixes
3. **Given** a plugin file exists but is malformed, **When** MythicMCP starts, **Then** the system logs a warning but continues to load other valid plugins

---

### User Story 2 - Execute Agent Commands on Callbacks (Priority: P2)

A security operator wants to execute agent-specific commands on a callback. They should be able to issue a command (like `apollo_shell`) targeting a specific callback ID, and receive the task results.

**Why this priority**: Once tools are loaded, operators need to actually execute them against targets to get value from the system.

**Independent Test**: Can be tested by issuing an agent command against an active callback and verifying the task is created and results are returned.

**Acceptance Scenarios**:

1. **Given** an active Apollo callback with ID 5, **When** the operator calls `apollo_shell` with callback_id=5 and command="whoami", **Then** a task is created in Mythic and results are returned
2. **Given** a callback using a different agent type than the tool, **When** the operator calls an incompatible tool, **Then** the system returns a clear error indicating agent type mismatch
3. **Given** a command that produces large output, **When** the operator executes it, **Then** results are returned in manageable chunks or summarized appropriately

---

### User Story 3 - Install New Agent Plugins (Priority: P3)

A security operator or administrator wants to add support for a new Mythic agent (e.g., Poseidon) to their MythicMCP installation. They should be able to install a plugin package that adds that agent's tools.

**Why this priority**: Extensibility ensures the system can grow with the Mythic ecosystem, but initial deployment can work with bundled plugins.

**Independent Test**: Can be tested by placing a new plugin file in the plugins directory and restarting MythicMCP, then verifying new tools appear.

**Acceptance Scenarios**:

1. **Given** a valid Poseidon plugin file, **When** the operator places it in the plugins directory and restarts MythicMCP, **Then** Poseidon-specific tools become available
2. **Given** no plugins are installed, **When** MythicMCP starts, **Then** only core tools are available and the system functions normally
3. **Given** a plugin with conflicting tool names, **When** MythicMCP loads plugins, **Then** tools are namespaced by agent name to prevent conflicts

---

### Edge Cases

- What happens when a plugin references a Mythic command that doesn't exist on the server? → Return clear error message from Mythic
- How does the system handle plugin updates? → New version replaces old on restart
- What happens when a callback disconnects mid-command? → Return timeout/disconnect error from Mythic
- How are plugin dependencies managed? → Plugins are self-contained, no external dependencies beyond core MythicMCP
- What if the Mythic server doesn't have the agent type installed? → Tools load but execution returns "agent type not available" error

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support loading agent plugins at startup from a designated plugins directory
- **FR-002**: System MUST namespace plugin tools by agent name (e.g., `apollo_shell`, `arachne_download`) to prevent naming conflicts
- **FR-003**: System MUST expose plugin tools through the MCP protocol alongside core tools
- **FR-004**: System MUST validate that a command is compatible with a callback's agent type before execution
- **FR-005**: System MUST create tasks in Mythic when agent commands are executed and return task results
- **FR-006**: System MUST handle plugin loading errors gracefully without crashing (log warning, skip invalid plugin)
- **FR-007**: System MUST provide a way to list which agent plugins are currently loaded
- **FR-008**: System MUST pass callback context (callback_id) to plugin tools for execution
- **FR-009**: System MUST support plugin tools with various parameter types (strings, integers, booleans, optional parameters)
- **FR-010**: System MUST timeout long-running commands with a configurable timeout (30-300 seconds, default 60s) and return partial results if available

### Key Entities

- **Plugin**: A self-contained module that defines tools for a specific Mythic agent type (Apollo, Arachne, Poseidon, etc.). Contains agent name, supported commands, and tool definitions.
- **Agent Tool**: A command that can be executed on a callback, mapped from a Mythic agent's command set. Has name, description, parameters, and agent type.
- **Task**: A Mythic task created when executing an agent tool, containing command parameters and results.
- **Callback**: An active agent session that tools are executed against. Has an associated agent type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can execute agent-specific commands within 5 seconds of issuing the request (excluding Mythic task execution time)
- **SC-002**: Plugin loading adds less than 2 seconds to MythicMCP startup time per plugin
- **SC-003**: At least 10 commonly-used commands for Apollo and Arachne agents are accessible as MCP tools in initial release
- **SC-004**: System handles 10 concurrent command executions without degradation
- **SC-005**: Invalid plugin files do not prevent system startup or affect other plugins
- **SC-006**: Operators can identify which agent type a tool belongs to by its name prefix

## Clarifications

### Session 2026-01-26

- Q: What should the command timeout behavior be? → A: Configurable timeout (30-300 seconds) with 60s default

## Assumptions

- Plugins will be distributed as files that can be placed in a plugins directory (no package manager required for MVP)
- The mythic Python library provides sufficient APIs to execute agent commands and retrieve results
- Agent tool parameters can be mapped to MCP tool parameters without loss of functionality
- Operators have appropriate Mythic permissions to execute commands on callbacks
- Initial release will include plugins for Apollo and Arachne agents; others can be added later
- Each plugin will define a subset of the most useful commands for its agent type (not necessarily 100% coverage)
