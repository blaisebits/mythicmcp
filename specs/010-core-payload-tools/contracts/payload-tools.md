# MCP Tool Contracts: Payload Tools

**Feature**: 010-core-payload-tools
**Date**: 2026-03-15

## core_list_payloads

List all payloads in the current operation.

**Parameters**: None
**Returns**: `ListPayloadsResponse`
**Errors**: McpError (no operation set, connection error)

```
Tool: core_list_payloads
Input: {}
Output: {
  payloads: [
    {uuid, agent_type, build_phase, description, deleted, auto_generated, creation_time, c2_profiles: [{name, is_p2p, running}]}
  ],
  count: int,
  retrieved_at: datetime
}
```

---

## core_get_payload

Get detailed information about a specific payload.

**Parameters**:
- `payload_uuid: string` (required) — UUID of the payload

**Returns**: `GetPayloadResponse`
**Errors**: McpError (not found, no operation, connection error)

```
Tool: core_get_payload
Input: {payload_uuid: "abc-123"}
Output: {
  payload: {uuid, agent_type, build_phase, build_message, build_stderr, callback_alert, description, deleted, auto_generated, creation_time, operator, file_uuid, filename, os, c2_profiles: [{name, is_p2p, running}]},
  retrieved_at: datetime
}
```

---

## core_create_payload

Create and build a new standard payload.

**Parameters**:
- `payload_type_name: string` (required) — Agent type (e.g., "apollo", "poseidon")
- `filename: string` (required) — Output filename
- `operating_system: string` (required) — Target OS (e.g., "Windows", "Linux", "macOS")
- `c2_profiles: string` (required) — JSON: `[{"c2_profile": "http", "c2_profile_parameters": {"callback_host": "https://...", ...}}]`
- `description: string` (optional, default "") — Payload description
- `commands: string` (optional, default "") — JSON array of command names: `["shell", "ls", "cat"]`
- `build_parameters: string` (optional, default "") — JSON: `[{"name": "param", "value": "val"}]`
- `include_all_commands: bool` (optional, default false) — Include all commands for the agent type
- `timeout: int` (optional, default 300) — Build timeout in seconds (30-600)

**Returns**: `CreatePayloadResponse | CreatePayloadErrorResponse`

```
Tool: core_create_payload
Input: {
  payload_type_name: "apollo",
  filename: "agent.exe",
  operating_system: "Windows",
  c2_profiles: '[{"c2_profile": "http", "c2_profile_parameters": {"callback_host": "https://mythic.local", "callback_port": 443}}]',
  include_all_commands: true,
  timeout: 300
}
Output (success): {
  success: true,
  uuid: "abc-123",
  build_phase: "success",
  build_message: "Build completed successfully",
  retrieved_at: datetime
}
Output (error): {
  success: false,
  error: "Build failed: ...",
  error_type: "build_failed",
  uuid: "abc-123",
  retrieved_at: datetime
}
```

---

## core_download_payload

Download a built payload binary.

**Parameters**:
- `payload_uuid: string` (required) — UUID of the payload

**Returns**: `DownloadPayloadResponse | DownloadPayloadErrorResponse`

```
Tool: core_download_payload
Input: {payload_uuid: "abc-123"}
Output (success): {
  success: true,
  payload_uuid: "abc-123",
  filename: "agent.exe",
  content: "<base64>",
  size_bytes: 123456,
  retrieved_at: datetime
}
Output (error): {
  success: false,
  error: "Payload not found",
  error_type: "not_found",
  payload_uuid: "abc-123",
  retrieved_at: datetime
}
```

---

## core_check_payload_config

Validate a payload's C2 configuration against running profiles.

**Parameters**:
- `payload_uuid: string` (required) — UUID of the payload

**Returns**: `PayloadConfigCheckResponse`
**Errors**: McpError (not found, connection error)

```
Tool: core_check_payload_config
Input: {payload_uuid: "abc-123"}
Output: {
  payload_uuid: "abc-123",
  status: "success",
  error: "",
  output: "All C2 profiles configured correctly",
  retrieved_at: datetime
}
```

---

## core_payload_redirect_rules

Get redirect rules for a payload's C2 configuration.

**Parameters**:
- `payload_uuid: string` (required) — UUID of the payload

**Returns**: `PayloadConfigCheckResponse` (same shape as config check)
**Errors**: McpError (not found, connection error)

```
Tool: core_payload_redirect_rules
Input: {payload_uuid: "abc-123"}
Output: {
  payload_uuid: "abc-123",
  status: "success",
  error: "",
  output: "<redirect rules text>",
  retrieved_at: datetime
}
```
