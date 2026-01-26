<!--
=== SYNC IMPACT REPORT ===
Version change: (new) → 1.0.0
Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (5 principles)
  - Security & Authorization Requirements
  - MCP Protocol Compliance
  - Governance
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section compatible
  ✅ .specify/templates/spec-template.md - Requirements section compatible
  ✅ .specify/templates/tasks-template.md - Phase structure compatible
Follow-up TODOs: None
========================
-->

# MythicMCP Constitution

## Core Principles

### I. MCP Protocol First

All server functionality MUST be exposed through valid MCP protocol interfaces. Direct API
access bypassing the MCP layer is prohibited for external consumers.

- Tools, resources, and prompts MUST conform to MCP specification
- All MCP responses MUST include proper JSON-RPC 2.0 formatting
- Error responses MUST use standard MCP error codes
- Server MUST handle capability negotiation correctly

**Rationale**: MCP protocol compliance ensures interoperability with any MCP-compatible client
and prevents tight coupling to specific AI assistants.

### II. Async-Native Architecture

All I/O operations MUST use Python async/await patterns. Blocking calls are prohibited in
the request path.

- Mythic API calls MUST use the async `mythic` library functions
- WebSocket and HTTP transports MUST be non-blocking
- Long-running operations MUST support cancellation via MCP protocol
- Connection pooling SHOULD be used for Mythic server connections

**Rationale**: The Mythic Python library is async-only. Mixing sync/async creates deadlocks
and performance issues. MCP servers handle concurrent requests.

### III. Plugin Isolation

Agent-specific functionality MUST be implemented as plugins that are loaded dynamically.
Core MCP server code MUST NOT contain agent-specific logic.

- Each Mythic agent (Apollo, Poseidon, etc.) has its own plugin module
- Plugins register their tools/resources at server startup
- Plugin failures MUST NOT crash the core server
- Plugins MUST declare their required Mythic agent compatibility

**Rationale**: Mythic supports many agents with different capabilities. Plugin isolation
allows adding agent support without modifying core code.

### IV. Explicit Authorization Context

Every MCP tool that performs Mythic operations MUST require explicit authorization context.
Operations MUST NOT execute without confirming the caller understands the action.

- Tool descriptions MUST clearly state what Mythic operations will be performed
- Destructive operations (kill callback, delete file) MUST be clearly labeled
- Tools MUST validate that the target Mythic instance is reachable before execution
- Failed authorization MUST return descriptive errors, not silent failures

**Rationale**: Mythic is a C2 framework. Accidental or unauthorized operations can disrupt
active engagements or cause data loss.

### V. Fail-Safe Defaults

When configuration or parameters are ambiguous, the server MUST choose the safest option.
Silent failures are prohibited.

- Missing Mythic credentials MUST prevent server startup (not runtime errors)
- Network timeouts MUST have reasonable defaults (30s for queries, 5min for file transfers)
- Unknown agent types MUST be rejected, not silently ignored
- All errors MUST be logged with sufficient context for debugging

**Rationale**: Security tooling requires predictable behavior. Silent failures or permissive
defaults can mask serious issues during engagements.

## Security & Authorization Requirements

Access to Mythic operations through this MCP server requires proper authorization at
multiple levels:

- **Mythic Authentication**: Valid Mythic API token or username/password credentials
- **MCP Transport Security**: TLS SHOULD be used for production deployments
- **Operation Scoping**: Tools SHOULD support limiting operations to specific operations,
  callbacks, or agents when the use case permits

Credentials MUST NOT be logged, included in error messages, or exposed through MCP
tool responses. The server MUST use the Mythic library's built-in credential handling.

## MCP Protocol Compliance

This server implements the Model Context Protocol for AI assistant integration:

- **Tools**: Expose Mythic operations (list callbacks, task agents, retrieve files, etc.)
- **Resources**: Provide read access to Mythic data (operation info, agent configs, logs)
- **Prompts**: Offer guided workflows for common engagement tasks

All implementations MUST follow the MCP specification. When the specification is ambiguous,
prefer behavior consistent with the reference MCP SDK implementations.

## Governance

This constitution establishes non-negotiable rules for MythicMCP development. All code
changes, feature additions, and architectural decisions MUST comply.

**Amendment Process**:
1. Propose amendment with rationale in a pull request
2. Document impact on existing code and plugins
3. Update version number per semantic versioning
4. Obtain maintainer approval before merge

**Versioning Policy**:
- MAJOR: Principle removal, redefinition, or backward-incompatible governance change
- MINOR: New principle, new section, or materially expanded guidance
- PATCH: Clarifications, wording improvements, typo fixes

**Compliance Review**:
- All PRs MUST pass Constitution Check in implementation plans
- Plugin contributions MUST demonstrate principle compliance
- Violations require explicit justification in Complexity Tracking

**Version**: 1.0.0 | **Ratified**: 2026-01-25 | **Last Amended**: 2026-01-25
