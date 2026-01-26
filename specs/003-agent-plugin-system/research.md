# Research: Agent Plugin System

**Feature Branch**: `003-agent-plugin-system`
**Date**: 2026-01-26

## Research Tasks

### 1. Mythic Task Execution API

**Question**: How to programmatically execute agent commands and retrieve results?

**Decision**: Use `mythic.issue_task()` with `wait_for_complete=True` followed by `mythic.get_all_task_output()` for results.

**Rationale**: The Mythic Python library provides a comprehensive async API for task management:

```python
# Create and wait for task completion
task = await mythic.issue_task(
    mythic=mythic_instance,
    command_name="shell",
    parameters={"command": "whoami"},  # or string for command_line style
    callback_display_id=5,
    wait_for_complete=True,
    timeout=60,  # seconds
)

# Get task output
output = await mythic.get_all_task_output_by_id(
    mythic=mythic_instance,
    task_display_id=task["display_id"]
)
```

Key API functions:
- `issue_task()` - Creates task, optionally waits for completion
- `waitfor_task_complete()` - Subscribes to task status updates
- `get_all_task_output_by_id()` - Retrieves task output

**Alternatives considered**:
- `issue_task_and_waitfor_task_output()` - Convenience function, but less control over error handling
- Subscriptions - More complex, better for streaming scenarios not needed here

### 2. Agent Type Validation

**Question**: How to validate that a callback's agent type matches the plugin's required type?

**Decision**: Query callback's payload.payloadtype.name field via GraphQL and compare to plugin's declared agent_type.

**Rationale**: The callback data structure includes nested payload information:
```python
# From existing callbacks.py pattern
callback_data.get("payload", {}).get("payloadtype", {}).get("name", "")
```

The existing `core_get_callback` tool already fetches this data. Plugin executor can reuse this pattern.

**Alternatives considered**:
- Store agent type in callback summary cache - Adds state complexity
- Validate on Mythic server side - Server validates anyway, but client-side check provides better error messages

### 3. Plugin Discovery Mechanism

**Question**: How should plugins be discovered and loaded?

**Decision**: Use Python's standard import machinery with a well-defined interface. Builtin plugins live in `plugins/builtin/`, external plugins via entry points (future).

**Rationale**:
- Python module imports are well-understood and debuggable
- Entry points can be added later for pip-installed plugins
- Keeping it simple for MVP per spec assumptions

Plugin discovery flow:
1. At startup, scan `plugins/builtin/` for modules
2. Each module exports a class inheriting from `BaseAgentPlugin`
3. Registry instantiates each plugin and collects tool definitions
4. Tools are registered with FastMCP server

**Alternatives considered**:
- Plugin directory on filesystem (like Mythic agents) - Over-engineered for MVP
- YAML/JSON definitions - Loses Python flexibility for parameter validation
- Entry points only - Requires separate pip packages, harder for bundled plugins

### 4. FastMCP Dynamic Tool Registration

**Question**: How to register plugin tools dynamically with FastMCP?

**Decision**: Use `mcp.tool()` as a function (not decorator) to register tools at runtime.

**Rationale**: FastMCP's `@mcp.tool()` decorator can also be called as a function:

```python
# Decorator style (existing core tools)
@mcp.tool()
async def core_list_callbacks(...): ...

# Function style (dynamic registration)
mcp.tool()(plugin_tool_function)
# or
mcp.add_tool(plugin_tool_function)
```

This allows plugins to define tools that get registered after the MCP server is created but before it starts.

**Alternatives considered**:
- Pre-generate all tool functions at import time - Works but less flexible
- Register tools via lifespan context - FastMCP may not support mid-lifespan registration

### 5. Parameter Type Mapping

**Question**: How to map Mythic command parameters to MCP tool parameters?

**Decision**: Use Pydantic models for tool parameters, converted to JSON for Mythic's `parameters` argument.

**Rationale**: Mythic commands accept parameters in two forms:
- String (command_line style): `shell whoami`
- Dict (scripting style): `{"command": "whoami"}`

Pydantic models provide:
- Type validation at MCP layer
- Clear parameter documentation in MCP schema
- Easy JSON serialization for Mythic

Common Mythic parameter types map to Python:
| Mythic Type | Python/Pydantic |
|-------------|-----------------|
| String | str |
| Number | int |
| Boolean | bool |
| File | Not supported in MVP (requires file registration flow) |
| ChooseOne | Literal[...] or str with validation |

**Alternatives considered**:
- Pass raw strings - Loses MCP schema benefits
- Dynamic Pydantic model generation - Over-complex for MVP

### 6. Task Timeout Handling

**Question**: How should command timeouts be handled?

**Decision**: Use asyncio.wait_for() wrapping the Mythic API calls with configurable timeout from config.

**Rationale**:
- Mythic's `issue_task()` accepts a `timeout` parameter
- Additional asyncio.wait_for() ensures MCP doesn't hang indefinitely
- Returns partial results if available on timeout

```python
try:
    async with asyncio.timeout(config.command_timeout):
        task = await mythic.issue_task(..., timeout=config.command_timeout)
        output = await mythic.get_all_task_output_by_id(...)
        return output
except asyncio.TimeoutError:
    # Return partial results or timeout error
    return {"error": "Command timed out", "partial_results": ...}
```

**Alternatives considered**:
- Rely only on Mythic's timeout - Doesn't cover network issues
- Fire-and-forget with polling - More complex, not needed for MVP

### 7. Tool Namespacing Strategy

**Question**: How to namespace plugin tools to avoid conflicts?

**Decision**: Prefix all plugin tools with `{agent_name}_` (e.g., `apollo_shell`, `arachne_download`).

**Rationale**:
- Clear identification of which agent the tool targets (SC-006)
- Prevents conflicts between agents with same command names (FR-002)
- Consistent with spec examples

The plugin base class enforces this:
```python
class BaseAgentPlugin:
    agent_name: str = "apollo"

    def get_tool_name(self, command_name: str) -> str:
        return f"{self.agent_name}_{command_name}"
```

**Alternatives considered**:
- Nested namespaces (`agents.apollo.shell`) - MCP doesn't support hierarchical tool names
- No prefix with conflict detection - Harder to understand for operators

## Summary

All research questions have been resolved. Key decisions:
1. Use `mythic.issue_task()` with `wait_for_complete=True` for synchronous execution
2. Validate agent type via callback's payload.payloadtype.name field
3. Python module imports for plugin discovery, builtin plugins bundled
4. FastMCP `mcp.tool()` function for dynamic tool registration
5. Pydantic models for parameters, converted to dict for Mythic
6. asyncio.timeout + Mythic timeout for dual-layer timeout handling
7. `{agent_name}_` prefix for all plugin tools
