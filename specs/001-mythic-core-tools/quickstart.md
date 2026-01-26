# Quickstart: Mythic Framework Core Tools

**Feature**: 001-mythic-core-tools
**Date**: 2026-01-25

## Prerequisites

- Python 3.10+
- Access to a Mythic C2 server (v3.3+)
- Mythic API token or username/password credentials

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mythicmcp

# Install dependencies
pip install -e ".[dev]"
```

## Configuration

Set environment variables for Mythic connection:

```bash
# Option 1: API Token (recommended for production)
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_API_TOKEN="your-api-token-here"

# Option 2: Username/Password (for development)
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_USERNAME="admin"
export MYTHIC_PASSWORD="your-password"
```

## Running the Server

```bash
# Run MCP server (stdio transport)
python -m mythicmcp.server
```

## Using with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mythicmcp": {
      "command": "python",
      "args": ["-m", "mythicmcp.server"],
      "env": {
        "MYTHIC_SERVER_URL": "https://mythic.local:7443",
        "MYTHIC_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

## Available Tools

### core_list_callbacks

List all active callbacks in the current operation.

**Example prompt**: "Show me all active callbacks"

**Response**:
```
Found 3 active callbacks:

1. WORKSTATION-01 (apollo)
   User: CORP\john.doe
   IP: 192.168.1.50
   Integrity: High

2. SERVER-DB (poseidon)
   User: SYSTEM
   IP: 192.168.1.10
   Integrity: System

3. LAPTOP-SALES (apollo)
   User: CORP\jane.smith
   IP: 192.168.1.75
   Integrity: Medium
```

### core_get_callback

Get detailed information about a specific callback.

**Example prompt**: "Get details for callback 1"

**Response**:
```
Callback 1: WORKSTATION-01

Host: WORKSTATION-01.corp.local
User: CORP\john.doe
Domain: CORP
IP: 192.168.1.50 (external: 203.0.113.50)
OS: Windows 10 Pro (x64)
Process: explorer.exe (PID 1234)
Integrity: High (3)
Agent: apollo
Description: Initial access via phishing
```

### core_get_operation

Get current operation information.

**Example prompt**: "What operation am I in?"

**Response**:
```
Operation: Sunrise

Created: 2026-01-20
Status: Active

Operators:
- admin (Admin)
- operator1
- operator2
```

### core_check_connection

Verify Mythic server connectivity.

**Example prompt**: "Check if Mythic is connected"

**Response (success)**:
```
✓ Connected to Mythic server
  Server: mythic.local:7443
  Operation: Sunrise
  Authenticated: Yes
```

**Response (failure)**:
```
✗ Connection failed
  Server: mythic.local:7443
  Error: Connection refused

  Troubleshooting:
  - Verify server URL is correct
  - Check if Mythic server is running
  - Ensure network connectivity
```

## Testing

```bash
# Run all tests
pytest

# Run with real Mythic server
pytest --mythic-server=https://mythic.local:7443 --mythic-token=your-token

# Run unit tests only (no Mythic required)
pytest tests/unit/
```

## Troubleshooting

### "No current operation set"

The Mythic user does not have a current operation selected. In Mythic UI:
1. Go to Operations
2. Click on an operation
3. Click "Set as Current"

### "Authentication failed"

- Verify `MYTHIC_API_TOKEN` or `MYTHIC_USERNAME`/`MYTHIC_PASSWORD` are set
- Check token/credentials are valid in Mythic UI
- Ensure token has not expired

### "Cannot reach Mythic server"

- Verify `MYTHIC_SERVER_URL` is correct
- Check Mythic server is running (`./mythic-cli status`)
- Verify network connectivity (firewall, VPN)
- SSL/TLS is currently disabled - ensure URL matches server config
