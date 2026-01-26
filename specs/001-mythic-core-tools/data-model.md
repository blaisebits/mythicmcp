# Data Model: Mythic Framework Core Tools

**Feature**: 001-mythic-core-tools
**Date**: 2026-01-25

## Overview

This feature is stateless - all data is retrieved from the Mythic server via GraphQL queries. The models below represent the structure of data returned by MCP tools.

## Entities

### Callback

Represents a connection from a compromised host to Mythic.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | integer | Internal callback ID | Mythic |
| `display_id` | integer | Human-readable callback number | Mythic |
| `hostname` | string | Target hostname | `host` field |
| `username` | string | User context | `user` field |
| `domain` | string | Domain name (Windows) | Mythic |
| `internal_ip` | string | Internal IP address | `ip` field |
| `external_ip` | string | External/NAT IP | Mythic |
| `os` | string | Operating system | Mythic |
| `architecture` | string | CPU architecture (x64, arm64) | Mythic |
| `process_id` | integer | Process ID | `pid` field |
| `process_name` | string | Process name | Mythic |
| `integrity_level` | integer | Windows integrity (0-4) | Mythic |
| `agent_type` | string | Payload type name | `payload.payloadtype.name` |
| `description` | string | Callback description | Mythic |
| `last_checkin` | datetime | Last callback checkin | Computed from activity |
| `active` | boolean | Whether callback is active | Mythic (filter) |

**Integrity Levels** (Windows):
- 0: Untrusted
- 1: Low
- 2: Medium
- 3: High
- 4: System

### Operation

Represents a Mythic engagement context.

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Operation ID |
| `name` | string | Operation name |
| `created_at` | datetime | Creation timestamp |
| `admin_id` | integer | Admin operator ID |
| `complete` | boolean | Whether operation is complete |

### Operator

Represents a Mythic user.

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Operator ID |
| `username` | string | Operator username |
| `admin` | boolean | Whether operator is admin |
| `active` | boolean | Whether operator is active |

### ConnectionStatus

Represents the result of a connectivity check.

| Field | Type | Description |
|-------|------|-------------|
| `connected` | boolean | Whether connection succeeded |
| `server_url` | string | Mythic server URL |
| `authenticated` | boolean | Whether authentication succeeded |
| `current_operation` | string | Name of current operation (if set) |
| `error` | string | Error message (if failed) |
| `timestamp` | datetime | When check was performed |

## Relationships

```
Operation (1) ──────< (many) Callback
    │
    └──< (many) Operator (via operatoroperation join)
```

- An **Operation** contains many **Callbacks**
- An **Operation** has many **Operators** assigned
- A **Callback** belongs to one **Operation**
- An **Operator** can access multiple **Operations**

## Response Schemas

### ListCallbacksResponse

```json
{
  "callbacks": [
    {
      "id": 1,
      "display_id": 1,
      "hostname": "WORKSTATION-01",
      "username": "john.doe",
      "agent_type": "apollo",
      "os": "Windows 10",
      "internal_ip": "192.168.1.50",
      "integrity_level": 3,
      "process_name": "explorer.exe",
      "active": true
    }
  ],
  "count": 1,
  "retrieved_at": "2026-01-25T12:00:00Z"
}
```

### GetCallbackResponse

```json
{
  "callback": {
    "id": 1,
    "display_id": 1,
    "hostname": "WORKSTATION-01",
    "username": "john.doe",
    "domain": "CORP",
    "internal_ip": "192.168.1.50",
    "external_ip": "203.0.113.50",
    "os": "Windows 10",
    "architecture": "x64",
    "process_id": 1234,
    "process_name": "explorer.exe",
    "integrity_level": 3,
    "agent_type": "apollo",
    "description": "Initial callback from phishing",
    "active": true
  },
  "retrieved_at": "2026-01-25T12:00:00Z"
}
```

### GetOperationResponse

```json
{
  "operation": {
    "id": 1,
    "name": "Operation Sunrise",
    "created_at": "2026-01-20T08:00:00Z",
    "complete": false
  },
  "operators": [
    {"username": "admin", "admin": true},
    {"username": "operator1", "admin": false}
  ],
  "retrieved_at": "2026-01-25T12:00:00Z"
}
```

### CheckConnectionResponse

```json
{
  "connected": true,
  "server_url": "https://mythic.local:7443",
  "authenticated": true,
  "current_operation": "Operation Sunrise",
  "timestamp": "2026-01-25T12:00:00Z"
}
```

## Validation Rules

### Callback ID
- Must be a positive integer
- Must exist in the current operation

### Timestamps
- All timestamps in ISO 8601 format with UTC timezone
- `retrieved_at` added to all responses per FR-008

### Credential Handling
- Credentials never included in any response
- Server URL included but port/path only (no auth params)
