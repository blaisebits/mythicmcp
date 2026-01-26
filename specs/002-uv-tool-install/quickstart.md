# Quickstart: MythicMCP Installation

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed on your system
- Access to a Mythic C2 server
- Mythic API token or credentials

## Installation

### Install as a Global Tool

```bash
uv tool install mythicmcp
```

### Install from Git (Development)

```bash
uv tool install git+https://github.com/user/mythicmcp
```

### Upgrade to Latest Version

```bash
uv tool install --upgrade mythicmcp
```

## Configuration

MythicMCP requires connection credentials for your Mythic server. Set these environment variables:

### Option 1: API Token (Recommended)

```bash
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_API_TOKEN="your-api-token-here"
```

### Option 2: Username/Password

```bash
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_USERNAME="mythic_admin"
export MYTHIC_PASSWORD="your-password-here"
```

### Optional: Timeout Configuration

```bash
export MYTHIC_TIMEOUT=60  # seconds, default is 30
```

## Verify Installation

Run the server to verify it can connect:

```bash
mythicmcp
```

You should see:
```
Starting MythicMCP server...
Connected to Mythic server at https://mythic.local:7443
```

## Configure MCP Clients

### Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mythic": {
      "command": "mythicmcp",
      "env": {
        "MYTHIC_SERVER_URL": "https://mythic.local:7443",
        "MYTHIC_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Cursor

Add to Cursor's MCP server configuration:

```json
{
  "mythic": {
    "command": "mythicmcp",
    "env": {
      "MYTHIC_SERVER_URL": "https://mythic.local:7443",
      "MYTHIC_API_TOKEN": "your-api-token"
    }
  }
}
```

## Available Tools

Once connected, MythicMCP provides these tools:

| Tool | Description |
|------|-------------|
| `core_list_callbacks` | List all active callbacks in the operation |
| `core_get_callback` | Get details for a specific callback |
| `core_get_operation` | Get current operation information |
| `core_check_connection` | Verify Mythic server connectivity |

## Troubleshooting

### "MYTHIC_SERVER_URL is required"

Set the `MYTHIC_SERVER_URL` environment variable to your Mythic server address.

### "Either MYTHIC_API_TOKEN or both MYTHIC_USERNAME and MYTHIC_PASSWORD are required"

Provide authentication credentials. API token is recommended.

### Connection Timeout

Increase the timeout: `export MYTHIC_TIMEOUT=120`

### Server Not Reachable

Verify:
1. Mythic server is running
2. Network connectivity to the server
3. Correct URL (include port, usually 7443)
