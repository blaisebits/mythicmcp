# Data Model: Core Payload Tools

**Feature**: 010-core-payload-tools
**Date**: 2026-03-15

## Entities

### PayloadSummary (list view)

Used by `core_list_payloads` response.

| Field | Type | Source (GraphQL) | Description |
| ----- | ---- | ---------------- | ----------- |
| uuid | string | `uuid` | Payload UUID (primary identifier) |
| agent_type | string | `payloadtype.name` | Payload type name (e.g., "apollo") |
| build_phase | string | `build_phase` | Build status: "building", "success", "error" |
| description | string | `description` | Operator-provided description |
| deleted | bool | `deleted` | Whether payload has been deleted |
| auto_generated | bool | `auto_generated` | Whether Mythic auto-generated this payload |
| creation_time | datetime | `creation_time` | When payload was created |
| os | string | `os` | Target operating system |
| c2_profiles | list[C2ProfileSummary] | `payloadc2profiles` | Associated C2 profiles |

### PayloadDetail (detail view)

Used by `core_get_payload` response. Extends PayloadSummary.

| Field | Type | Source (GraphQL) | Description |
| ----- | ---- | ---------------- | ----------- |
| uuid | string | `uuid` | Payload UUID |
| agent_type | string | `payloadtype.name` | Payload type name |
| build_phase | string | `build_phase` | Build status |
| build_message | string | `build_message` | Build output message |
| build_stderr | string | `build_stderr` | Build stderr output |
| callback_alert | bool | `callback_alert` | Whether callback alerts are enabled |
| description | string | `description` | Operator-provided description |
| deleted | bool | `deleted` | Whether payload has been deleted |
| auto_generated | bool | `auto_generated` | Whether auto-generated |
| creation_time | datetime | `creation_time` | When payload was created |
| operator | string | `operator.username` | Who created it |
| file_uuid | string? | `filemetum.agent_file_id` | File UUID for download (null if build failed) |
| filename | string? | `filemetum.filename_utf8` | Built filename |
| c2_profiles | list[C2ProfileSummary] | `payloadc2profiles` | Associated C2 profiles |
| os | string | `os` | Target operating system |

### C2ProfileSummary

Nested in payload models.

| Field | Type | Source (GraphQL) | Description |
| ----- | ---- | ---------------- | ----------- |
| name | string | `c2profile.name` | Profile name (e.g., "http") |
| is_p2p | bool | `c2profile.is_p2p` | Whether this is a P2P profile |
| running | bool | `c2profile.running` | Whether the profile container is running |

### PayloadConfigCheckResult

Used by `core_check_payload_config` and `core_payload_redirect_rules` responses.

| Field | Type | Source | Description |
| ----- | ---- | ------ | ----------- |
| status | string | `status` | "success" or "error" |
| error | string | `error` | Error message if status is error |
| output | string | `output` | Result output text |

## Response Models

### ListPayloadsResponse
- `payloads: list[PayloadSummary]`
- `count: int`
- `retrieved_at: datetime` (UTC)

### GetPayloadResponse
- `payload: PayloadDetail`
- `retrieved_at: datetime` (UTC)

### CreatePayloadResponse (success)
- `success: bool = True`
- `uuid: string` — new payload UUID
- `build_phase: string` — terminal build status
- `build_message: string` — build output
- `retrieved_at: datetime` (UTC)

### CreatePayloadErrorResponse (error)
- `success: bool = False`
- `error: string`
- `error_type: string` — "no_operation", "build_failed", "connection_error", "timeout", "invalid_input"
- `uuid: string?` — payload UUID if available (e.g., timeout case)
- `retrieved_at: datetime` (UTC)

### DownloadPayloadResponse (success)
- `success: bool = True`
- `payload_uuid: string`
- `filename: string`
- `content: string` — base64-encoded binary
- `size_bytes: int`
- `retrieved_at: datetime` (UTC)

### DownloadPayloadErrorResponse (error)
- `success: bool = False`
- `error: string`
- `error_type: string` — "not_found", "build_incomplete", "connection_error", "no_operation"
- `payload_uuid: string`
- `retrieved_at: datetime` (UTC)

### PayloadConfigCheckResponse
- `payload_uuid: string`
- `status: string`
- `error: string`
- `output: string`
- `retrieved_at: datetime` (UTC)

## State Transitions

Payload `build_phase` lifecycle (managed by Mythic, read-only from MCP):

```
[created] → "building" → "success" (downloadable)
                       → "error" (not downloadable)
```

## Validation Rules

- `payload_uuid`: Non-empty string, trimmed
- `payload_type_name`: Non-empty string (validated by Mythic server)
- `filename`: Non-empty string (validated by Mythic server)
- `operating_system`: Non-empty string (validated by Mythic server)
- `c2_profiles` JSON: Must parse to `list[{c2_profile: str, c2_profile_parameters: dict}]`
- `build_parameters` JSON: Must parse to `list[{name: str, value: str}]`
- `timeout`: Integer >= 30, <= 600 (default 300)
