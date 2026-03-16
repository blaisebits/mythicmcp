# Research: Core Payload Tools

**Feature**: 010-core-payload-tools
**Date**: 2026-03-15

## R1: Mythic Payload API Surface

**Decision**: Use the `mythic` Python library's built-in payload functions for list, get, create, and download. Use `execute_custom_query` for config check and redirect rules.

**Rationale**: The `mythic` library (0.2.10) provides async functions that map directly to our tool needs:
- `mythic.get_all_payloads()` → list (returns all payloads, supports `custom_return_attributes`)
- `mythic.get_payload_by_uuid()` → get detail (supports `custom_return_attributes`)
- `mythic.create_payload()` → create (supports `return_on_complete`, `timeout`, `include_all_commands`)
- `mythic.download_payload()` → download (resolves file UUID internally, returns bytes)
- `mythic.payload_check_config()` → config check (returns `{status, error, output}`)
- `mythic.payload_redirect_rules()` → redirect rules (returns `{status, error, output}`)

**Alternatives considered**:
- Raw GraphQL queries for all operations → rejected; library already handles subscription-based build waiting and file download resolution.

## R2: GraphQL Fragment for Payload Data

**Decision**: Use the library's `payload_data_fragment` for get-detail, and a custom lighter fragment for list.

**Rationale**: The full `payload_data_fragment` includes: `build_message`, `build_phase`, `build_stderr`, `callback_alert`, `creation_time`, `id`, `operator{id,username}`, `uuid`, `description`, `deleted`, `auto_generated`, `payloadtype{id,name}`, `filemetum{agent_file_id,filename_utf8,id}`, `payloadc2profiles{c2profile{running,name,is_p2p,container_running}}`. This is ideal for detail view.

For list view, `get_all_payloads()` with `custom_return_attributes` can return a lighter set: `uuid`, `build_phase`, `description`, `deleted`, `auto_generated`, `creation_time`, `payloadtype{name}`, `payloadc2profiles{c2profile{name,running,is_p2p}}`.

**Alternatives considered**:
- Full fragment for list too → rejected; unnecessary data volume for summary view.

## R3: Create Payload Input Structure

**Decision**: Accept C2 profiles as a JSON string parameter (list of objects with `c2_profile` name and `c2_profile_parameters` dict). Build parameters as a JSON string (list of `{name, value}` dicts).

**Rationale**: MCP tools accept primitive types (string, int, bool). Complex structures like C2 profile configs must be serialized as JSON strings. The tool will parse and validate before passing to the Mythic API. This matches how the integration test helper already structures the data.

**Alternatives considered**:
- Separate tools per C2 profile → rejected; overly fragmented, doesn't match the single-call creation UX.
- Flattened parameters → rejected; C2 profiles have variable parameters per profile type.

## R4: Build Timeout Default

**Decision**: Default timeout of 300 seconds (5 minutes) for payload creation.

**Rationale**: Integration tests use 300s. Payload builds involve container compilation (Go, C#, etc.) which can take 1-3 minutes. The existing constitution specifies "5min for file transfers" as a reasonable default for long operations. 300s provides headroom without excessive waiting.

**Alternatives considered**:
- 60s (existing task executor default) → rejected; too short for compilation-heavy payloads.
- No timeout → rejected; violates Constitution Principle V (Fail-Safe Defaults).

## R5: Error Handling Pattern

**Decision**: Follow the files.py two-tier pattern: typed exception classes in the tool module, caught and converted to error response models or McpError at the entry point layer.

**Rationale**: Consistent with existing `files.py` (uses response union types like `Response | ErrorResponse`) and `callbacks.py`/`operations.py` (raises `McpError`). For payload tools, use the response union pattern (matching files.py) since create/download can fail in expected ways that should return structured error data rather than MCP-level errors.

For list/get tools, use McpError pattern (matching callbacks.py) since errors are unexpected failures.

**Alternatives considered**:
- All McpError → rejected; loses structured error type information for create/download.
- All response unions → acceptable but inconsistent with read-only tools pattern.

## R6: Module Organization

**Decision**: Create a single new module `src/mythicmcp/tools/payloads.py` following the same structure as `files.py`.

**Rationale**: Files.py handles 4 tools in one module and is the closest analog (upload/download + list operations). Payloads has 6 tools but similar complexity per tool. A single module keeps the codebase flat and avoids unnecessary subdirectories.

**Alternatives considered**:
- Split into `payloads_read.py` and `payloads_write.py` → rejected; unnecessary split for 6 functions.
