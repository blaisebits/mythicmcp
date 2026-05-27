# MythicMCP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP 1.26+](https://img.shields.io/badge/MCP-1.26+-green.svg)](https://modelcontextprotocol.io/)

MythicMCP is an MCP server for the [Mythic](https://github.com/its-a-feature/Mythic) C2 framework. It gives MCP clients a practical tool surface for working with Mythic operations, callbacks, tasks, files, payloads, C2 profiles, and agent-specific commands.

## Features

- Core Mythic tools for:
  - connection and operation context
  - callbacks and task output
  - uploaded/downloaded files
  - payload creation and download
  - C2 profile discovery and saved instances
- Generic callback command workflow for any loaded Mythic command:
  - `core_list_callback_commands`
  - `core_get_callback_command`
  - `core_execute_callback_command`
- Bundled typed plugin toolsets for:
  - Apollo
  - Poseidon
  - Arachne
- YAML-driven plugin system for adding more agents without writing Python handlers

## Requirements

- Python `3.10+`
- [`uv`](https://docs.astral.sh/uv/)
- Access to a Mythic server
- Mythic API token or username/password

## Installation
Install from GitHub:

```bash
uv tool install git+https://github.com/blaisebits/mythicmcp
```

Upgrade:

```bash
uv tool install --upgrade git+https://github.com/blaisebits/mythicmcp
```

Verify:

```bash
mythicmcp --help
```

## Configuration

Set Mythic connection settings in your MCP client config or shell environment.

API token:

```bash
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_API_TOKEN="your-api-token"
```

Username/password:

```bash
export MYTHIC_SERVER_URL="https://mythic.local:7443"
export MYTHIC_USERNAME="mythic_admin"
export MYTHIC_PASSWORD="your-password"
```

Optional:

```bash
export MYTHIC_TIMEOUT=60
export MYTHIC_AGENTS=apollo,poseidon
export MYTHIC_HOTLOAD=1
```

Environment reference:

| Variable | Required | Description |
|---|---|---|
| `MYTHIC_SERVER_URL` | Yes | Mythic server URL |
| `MYTHIC_API_TOKEN` | Conditional | API token auth |
| `MYTHIC_USERNAME` | Conditional | Username auth |
| `MYTHIC_PASSWORD` | Conditional | Password auth |
| `MYTHIC_TIMEOUT` | No | Query timeout in seconds |
| `MYTHIC_AGENTS` | No | Preload agent toolsets at startup |
| `MYTHIC_HOTLOAD` | No | Enable dynamic load/unload tools |
| `MYTHIC_DEV` | No | Enable development-only tools |

## MCP Client Setup

### Claude Desktop

Add to the Claude Desktop MCP config:

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

### Local example config

This repo includes [`.mcp.json.example`](./.mcp.json.example) for local testing.

## Tool Surface

High-value core tools:

- Connection and ops:
  - `core_check_connection`
  - `core_list_operations`
  - `core_set_operation`
  - `core_get_operation`
- Callbacks and tasks:
  - `core_list_callbacks`
  - `core_get_callback`
  - `core_list_callback_tasks`
  - `core_get_task_output`
  - `core_get_task_callback`
- Generic command execution:
  - `core_list_callback_commands`
  - `core_get_callback_command`
  - `core_execute_callback_command`
- Files and payloads:
  - `core_upload_file`
  - `core_download_file`
  - `core_list_uploaded_files`
  - `core_list_payloads`
  - `core_create_payload`
  - `core_download_payload`
- C2 profiles:
  - `core_list_c2_profiles`
  - `core_get_c2_profile_parameters`
  - `core_create_c2_instance`
  - `core_list_c2_instances`

Bundled agent-specific tools are also exposed for Apollo, Poseidon, and Arachne.

## Usage Notes

- Use `callback_id` as the canonical callback identifier for follow-on work.
- `display_id` is returned for UI correlation only.
- For generic callback commands, prefer `argument_mode`, `execution_usage`, and `example_arguments` over `usage`.
- In a fresh session, start with `core_check_connection`, then `core_set_operation` if needed.

## Development

Install dev deps:

```bash
uv sync --all-extras
```

Run unit tests:

```bash
uv run pytest tests/unit -q
```

Build packages:

```bash
uv build
```

## Docker Codex Harness

The repo includes a Docker harness for testing MythicMCP changes in a fresh Codex session.

Build:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker\build-codex-image.ps1
```

Interactive session:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker\run-codex-manual.ps1
```

One-shot prompt:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker\run-codex-manual.ps1 --prompt "Call core_check_connection and summarize the result."
```

Integration tests in Docker:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker\run-integration-tests.ps1 --pipeline
```

## Troubleshooting

Missing server URL:

```text
MYTHIC_SERVER_URL is required
```

Missing auth:

```text
Either MYTHIC_API_TOKEN or both MYTHIC_USERNAME and MYTHIC_PASSWORD are required
```

MCP startup issues:

- verify `mythicmcp --help` works
- verify env vars are set in the MCP client config, not only your shell
- use `core_check_connection` first to confirm auth and current operation

## License

MIT. See [LICENSE](./LICENSE).
