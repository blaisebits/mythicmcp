# MCP Tool Contracts: Mythic Framework Core Tools

**Feature**: 001-mythic-core-tools
**Date**: 2026-01-25

## Overview

This document defines the MCP tool contracts for the Mythic Framework Core Tools. Each tool follows the Model Context Protocol specification with JSON Schema for parameters and return types.

---

## Tool: `core_list_callbacks`

**Description**: List all active callbacks (compromised hosts) in the current Mythic operation. Returns hostname, username, agent type, and last check-in time for each callback.

### Parameters

None required.

### Input Schema

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

### Response

```json
{
  "type": "object",
  "properties": {
    "callbacks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "display_id": {"type": "integer"},
          "hostname": {"type": "string"},
          "username": {"type": "string"},
          "agent_type": {"type": "string"},
          "os": {"type": "string"},
          "internal_ip": {"type": "string"},
          "integrity_level": {"type": "integer"},
          "process_name": {"type": "string"},
          "active": {"type": "boolean"}
        }
      }
    },
    "count": {"type": "integer"},
    "retrieved_at": {"type": "string", "format": "date-time"}
  },
  "required": ["callbacks", "count", "retrieved_at"]
}
```

### Errors

| Condition | Error Message |
|-----------|---------------|
| Not authenticated | "Mythic authentication failed: [details]" |
| Server unreachable | "Cannot reach Mythic server: [details]" |
| No operation set | "No current operation set. Configure operation in Mythic." |

---

## Tool: `core_get_callback`

**Description**: Get detailed information about a specific Mythic callback by ID. Returns full callback configuration including host details, process info, integrity level, and agent configuration.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `callback_id` | integer | Yes | The callback ID to retrieve |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "callback_id": {
      "type": "integer",
      "description": "The callback ID to retrieve"
    }
  },
  "required": ["callback_id"]
}
```

### Response

```json
{
  "type": "object",
  "properties": {
    "callback": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "display_id": {"type": "integer"},
        "hostname": {"type": "string"},
        "username": {"type": "string"},
        "domain": {"type": "string"},
        "internal_ip": {"type": "string"},
        "external_ip": {"type": "string"},
        "os": {"type": "string"},
        "architecture": {"type": "string"},
        "process_id": {"type": "integer"},
        "process_name": {"type": "string"},
        "integrity_level": {"type": "integer"},
        "agent_type": {"type": "string"},
        "description": {"type": "string"},
        "active": {"type": "boolean"}
      }
    },
    "retrieved_at": {"type": "string", "format": "date-time"}
  },
  "required": ["callback", "retrieved_at"]
}
```

### Errors

| Condition | Error Message |
|-----------|---------------|
| Callback not found | "Callback with ID [id] not found" |
| Not authenticated | "Mythic authentication failed: [details]" |
| Access denied | "Access denied to callback [id]" |

---

## Tool: `core_get_operation`

**Description**: Get information about the current Mythic operation including name, creation date, and list of assigned operators.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `operation_id` | integer | No | Specific operation ID (defaults to current) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation_id": {
      "type": "integer",
      "description": "Specific operation ID (defaults to current operation)"
    }
  },
  "required": []
}
```

### Response

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "complete": {"type": "boolean"}
      }
    },
    "operators": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "username": {"type": "string"},
          "admin": {"type": "boolean"}
        }
      }
    },
    "retrieved_at": {"type": "string", "format": "date-time"}
  },
  "required": ["operation", "operators", "retrieved_at"]
}
```

### Errors

| Condition | Error Message |
|-----------|---------------|
| Operation not found | "Operation with ID [id] not found" |
| No current operation | "No current operation set" |
| Not authenticated | "Mythic authentication failed: [details]" |

---

## Tool: `core_check_connection`

**Description**: Verify connectivity and authentication status with the Mythic server. Use this to troubleshoot connection issues.

### Parameters

None required.

### Input Schema

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

### Response

```json
{
  "type": "object",
  "properties": {
    "connected": {"type": "boolean"},
    "server_url": {"type": "string"},
    "authenticated": {"type": "boolean"},
    "current_operation": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"}
  },
  "required": ["connected", "authenticated", "timestamp"]
}
```

### Error Response

When connection fails, returns structured error instead of raising:

```json
{
  "type": "object",
  "properties": {
    "connected": {"type": "boolean", "const": false},
    "error": {"type": "string"},
    "error_type": {
      "type": "string",
      "enum": ["connection_failed", "authentication_failed", "timeout"]
    },
    "server_url": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"}
  },
  "required": ["connected", "error", "error_type", "timestamp"]
}
```

---

## Common Patterns

### Timestamps

All responses include `retrieved_at` (or `timestamp` for status checks) in ISO 8601 format with UTC timezone:

```
"2026-01-25T12:00:00Z"
```

### Error Handling

Tools use MCP ToolError for errors. Error messages:
- Include context (what failed)
- Include actionable information (how to fix)
- Never include credentials or sensitive data

### Tool Descriptions

Per Constitution Principle IV, all tool descriptions clearly state what Mythic operation will be performed. This allows the AI assistant to inform users before invoking tools.
