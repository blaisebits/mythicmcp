# MCP Tool Contracts: Agent Plugin System

**Feature Branch**: `003-agent-plugin-system`
**Date**: 2026-01-26

## Core Plugin Management Tools

### list_plugins

Lists all loaded agent plugins.

**Tool Name**: `core_list_plugins`

**Parameters**: None

**Response Schema**:
```json
{
  "plugins": [
    {
      "agent_name": "apollo",
      "agent_description": "Apollo Windows C# agent",
      "tool_count": 10,
      "supported_os": ["Windows"]
    }
  ],
  "total_count": 2,
  "load_errors": [
    {
      "plugin_path": "plugins/builtin/broken.py",
      "error": "Invalid plugin format"
    }
  ]
}
```

---

## Apollo Agent Tools

All Apollo tools are prefixed with `apollo_` and target Windows callbacks.

### apollo_shell

Execute a shell command via cmd.exe on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| command | string | yes | Shell command to execute |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 42,
  "output": "HOSTNAME\\username",
  "execution_time_ms": 1523.4
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Agent type mismatch: tool requires 'apollo' but callback 5 is 'arachne'",
  "error_type": "agent_mismatch",
  "callback_id": 5
}
```

### apollo_execute_assembly

Execute a .NET assembly on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| assembly_name | string | yes | Name of registered assembly (e.g., "Seatbelt.exe") |
| assembly_arguments | string | no | Arguments to pass to assembly |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 43,
  "output": "[Seatbelt output...]",
  "execution_time_ms": 5234.1
}
```

### apollo_download

Download a file from an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to file on target |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 44,
  "output": "Downloaded file: C:\\Users\\admin\\secret.txt (1234 bytes)",
  "execution_time_ms": 2341.5
}
```

### apollo_pwd

Get current working directory of an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 45,
  "output": "C:\\Users\\admin",
  "execution_time_ms": 523.2
}
```

### apollo_ls

List directory contents on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | no | Path to list (default: current directory) |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 46,
  "output": "Directory listing of C:\\Users\\admin\\...",
  "execution_time_ms": 834.7
}
```

### apollo_ps

List running processes on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 47,
  "output": "PID\tName\tUser\n...",
  "execution_time_ms": 1234.5
}
```

### apollo_cd

Change working directory on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to change to |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 48,
  "output": "Changed directory to C:\\Windows",
  "execution_time_ms": 412.3
}
```

### apollo_cat

Read file contents on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to file to read |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 49,
  "output": "[file contents]",
  "execution_time_ms": 723.4
}
```

### apollo_run

Execute a program on an Apollo callback without cmd.exe wrapper.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| executable | string | yes | Path to executable |
| arguments | string | no | Arguments to pass |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 50,
  "output": "[program output]",
  "execution_time_ms": 1523.6
}
```

### apollo_screenshot

Take a screenshot on an Apollo callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 51,
  "output": "Screenshot captured (1920x1080, 234KB)",
  "execution_time_ms": 2341.2
}
```

---

## Arachne Agent Tools

All Arachne tools are prefixed with `arachne_` and support ASPX/PHP/JSP webshells.

### arachne_shell

Execute a shell command on an Arachne webshell callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| command | string | yes | Command to execute |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 52,
  "output": "command output",
  "execution_time_ms": 1823.4
}
```

### arachne_download

Download a file from an Arachne webshell callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to file to download |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 53,
  "output": "Downloaded: /var/www/html/config.php (456 bytes)",
  "execution_time_ms": 2134.5
}
```

### arachne_upload

Upload a file to an Arachne webshell callback.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| remote_path | string | yes | Destination path on target |
| file_contents | string | yes | Base64-encoded file contents |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 54,
  "output": "Uploaded to /var/www/html/shell.php",
  "execution_time_ms": 1523.7
}
```

### arachne_pwd

Get current working directory of an Arachne webshell.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 55,
  "output": "/var/www/html",
  "execution_time_ms": 823.4
}
```

### arachne_ls

List directory contents on an Arachne webshell.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | no | Path to list (default: current directory) |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 56,
  "output": "drwxr-xr-x  2 www-data www-data 4096 Jan 26 10:00 .",
  "execution_time_ms": 934.5
}
```

### arachne_cd

Change working directory on an Arachne webshell.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to change to |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 57,
  "output": "Changed to /tmp",
  "execution_time_ms": 612.3
}
```

### arachne_rm

Remove a file on an Arachne webshell.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| path | string | yes | Path to file to remove |
| timeout | integer | no | Timeout in seconds (default: 60, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 58,
  "output": "Removed /tmp/test.txt",
  "execution_time_ms": 523.4
}
```

### arachne_execute_assembly

Execute a .NET assembly on an Arachne ASPX webshell (Windows only).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| callback_id | integer | yes | Target callback ID |
| assembly_name | string | yes | Name of registered assembly |
| assembly_arguments | string | no | Arguments to pass |
| timeout | integer | no | Timeout in seconds (default: 120, range: 30-300) |

**Response Schema**:
```json
{
  "success": true,
  "task_id": 59,
  "output": "[assembly output]",
  "execution_time_ms": 4523.6
}
```

---

## Common Error Types

All plugin tools return consistent error types:

| error_type | Description |
|------------|-------------|
| `agent_mismatch` | Callback's agent type doesn't match tool's required type |
| `callback_not_found` | Specified callback ID doesn't exist |
| `callback_inactive` | Callback exists but is not active |
| `execution_failed` | Task created but execution failed |
| `timeout` | Command exceeded timeout |
| `no_operation` | No current operation set in Mythic |
| `permission_denied` | Insufficient Mythic permissions |
