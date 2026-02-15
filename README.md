# MythicMCP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP 1.26+](https://img.shields.io/badge/MCP-1.26+-green.svg)](https://modelcontextprotocol.io/)

MCP server for the Mythic C2 Framework. Provides programmatic access to Mythic operations with a plugin system for agent-specific interactions.

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

### Verify Installation

```bash
which mythicmcp
```

You should see a path like `/home/user/.local/bin/mythicmcp`.

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

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MYTHIC_SERVER_URL` | Yes | Mythic server URL (e.g., `https://mythic.local:7443`) |
| `MYTHIC_API_TOKEN` | Conditional | API token (alternative to username/password) |
| `MYTHIC_USERNAME` | Conditional | Username (requires MYTHIC_PASSWORD) |
| `MYTHIC_PASSWORD` | Conditional | Password (requires MYTHIC_USERNAME) |
| `MYTHIC_TIMEOUT` | No | Query timeout in seconds (default: 30) |

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

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

Add to Cursor's MCP server configuration (Settings > MCP Servers):

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
| `core_get_callback` | Get details for a specific callback by ID |
| `core_get_operation` | Get current operation information |
| `core_check_connection` | Verify Mythic server connectivity |

## Troubleshooting

### "MYTHIC_SERVER_URL is required"

Set the `MYTHIC_SERVER_URL` environment variable to your Mythic server address:

```bash
export MYTHIC_SERVER_URL="https://mythic.local:7443"
```

### "Either MYTHIC_API_TOKEN or both MYTHIC_USERNAME and MYTHIC_PASSWORD are required"

Provide authentication credentials. API token is recommended:

```bash
export MYTHIC_API_TOKEN="your-api-token-here"
```

Or use username/password:

```bash
export MYTHIC_USERNAME="mythic_admin"
export MYTHIC_PASSWORD="your-password-here"
```

### Connection Timeout

Increase the timeout if your Mythic server is slow to respond:

```bash
export MYTHIC_TIMEOUT=120
```

### Server Not Reachable

Verify:
1. Mythic server is running
2. Network connectivity to the server
3. Correct URL (include port, usually 7443)
4. SSL certificate is valid or server URL uses correct protocol

### MCP Client Not Discovering Tools

1. Verify `mythicmcp` command is in your PATH: `which mythicmcp`
2. Check MCP client logs for connection errors
3. Ensure environment variables are set in the MCP configuration, not just your shell

## Development

### Install Development Dependencies

```bash
uv sync --all-extras
```

### Run Tests

```bash
uv run pytest
```

### Run Tests with Coverage

```bash
uv run pytest --cov
```

### Local MCP Testing

To test the MCP server locally with Claude Code or other MCP clients, copy the example config and fill in your credentials:

```bash
cp .mcp.json.example .mcp.json
```

Edit `.mcp.json` with your Mythic server URL and API token. This file is gitignored and will not be committed.

## License

MIT License - see LICENSE file for details.
