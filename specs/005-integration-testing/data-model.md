# Data Model: Integration Testing Pipeline

**Feature**: 005-integration-testing
**Date**: 2026-02-08

## YAML Configuration Schema

The YAML configuration file (`tests/integration/config.yaml`) is the single source of truth for all integration test parameters. It is validated at test startup using Pydantic models.

### Top-Level Structure

```yaml
# Mythic server connection
mythic:
  server_url: "https://10.5.10.10:7443"
  api_token: "eyJ..."            # Preferred auth method
  # OR username/password:
  # username: "mythic_admin"
  # password: "password123"
  timeout: 30                     # Connection timeout in seconds (default: 30)

# Timeout defaults (can be overridden per-agent or per-command)
timeouts:
  payload_generation: 300         # Seconds to wait for payload build (default: 300)
  callback_verification: 120      # Seconds to poll for new callback (default: 120)
  command_execution: 60           # Seconds per command execution (default: 60)
  polling_interval: 5             # Seconds between callback polls (default: 5)

# Agent type definitions
agents:
  - name: "apollo"
    payload_type: "apollo"
    os: "Windows"
    filename: "apollo_test.exe"
    c2_profiles:
      - c2_profile: "http"
        c2_profile_parameters:
          callback_host: "https://10.5.10.10"
          callback_port: 443
    build_parameters: []          # Optional build params
    description: "Apollo test payload"

  - name: "arachne"
    payload_type: "arachne"
    os: "Linux"
    filename: "arachne_test"
    c2_profiles:
      - c2_profile: "http"
        c2_profile_parameters:
          callback_host: "https://10.5.10.10"
          callback_port: 443
    build_parameters: []
    description: "Arachne test payload"

# Target system definitions
targets:
  - name: "windows-target"
    hostname: "WIN11-PC"
    os: "Windows"
    callback_id: 1                # Pre-existing callback ID for file ops
    upload_path: "C:\\Users\\Public\\test_payload.exe"
    agents:                       # Explicit agent mapping
      - "apollo"

  - name: "linux-target"
    hostname: "debian-vm"
    os: "Linux"
    callback_id: 2
    upload_path: "/tmp/test_payload"
    agents:
      - "arachne"

# Test commands per agent type
test_commands:
  apollo:
    - command: "shell"
      parameters:
        command: "whoami"
      expected_output: "\\"          # Substring match (contains backslash = domain\user)
      timeout: 60
    - command: "pwd"
      parameters: {}
      expected_output: "C:\\"
      timeout: 60

  arachne:
    - command: "shell"
      parameters:
        command: "id"
      expected_output: "uid="
      timeout: 60
    - command: "pwd"
      parameters: {}
      expected_output: "/"
      timeout: 60
```

## Pydantic Validation Models

### MythicConnectionConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| server_url | str | Yes | — | Mythic server URL (e.g., `https://host:port`) |
| api_token | str | No | None | API token (preferred over username/password) |
| username | str | No | None | Username (alternative to api_token) |
| password | str | No | None | Password (used with username) |
| timeout | int | No | 30 | Connection timeout in seconds |

**Validation**: Either `api_token` OR (`username` + `password`) must be provided.

### TimeoutConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| payload_generation | int | No | 300 | Max seconds for payload build |
| callback_verification | int | No | 120 | Max seconds to wait for callback |
| command_execution | int | No | 60 | Max seconds per command |
| polling_interval | int | No | 5 | Seconds between callback polls |

### AgentConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | str | Yes | — | Unique identifier for this agent config |
| payload_type | str | Yes | — | Mythic payload type name (e.g., "apollo") |
| os | str | Yes | — | Target OS for payload build (e.g., "Windows", "Linux") |
| filename | str | Yes | — | Filename for the generated payload |
| c2_profiles | list[C2ProfileConfig] | Yes | — | C2 profile configurations |
| build_parameters | list[BuildParam] | No | [] | Build-time parameters |
| description | str | No | "" | Payload description |

### C2ProfileConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| c2_profile | str | Yes | — | C2 profile name (e.g., "http") |
| c2_profile_parameters | dict[str, Any] | Yes | — | Profile-specific parameters |

### BuildParam

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | str | Yes | — | Build parameter name |
| value | str | Yes | — | Build parameter value |

### TargetConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | str | Yes | — | Human-readable target identifier |
| hostname | str | Yes | — | Expected hostname in callback metadata |
| os | str | Yes | — | Operating system (e.g., "Windows", "Linux") |
| callback_id | int | Yes | — | Pre-existing callback ID for file operations |
| upload_path | str | Yes | — | Filesystem path to upload payload to |
| agents | list[str] | Yes | — | Agent config names to test on this target |

**Validation**: Each agent name in `agents` must reference an existing entry in the top-level `agents` list.

### TestCommandConfig

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| command | str | Yes | — | Agent command name (e.g., "shell", "pwd") |
| parameters | dict[str, Any] | No | {} | Command parameters |
| expected_output | str | No | None | Substring or regex pattern to match in output |
| timeout | int | No | 60 | Command timeout in seconds |

### IntegrationTestConfig (top-level)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| mythic | MythicConnectionConfig | Yes | — | Mythic server connection |
| timeouts | TimeoutConfig | No | TimeoutConfig() | Default timeouts |
| agents | list[AgentConfig] | Yes | — | Agent type definitions |
| targets | list[TargetConfig] | Yes | — | Target system definitions |
| test_commands | dict[str, list[TestCommandConfig]] | Yes | — | Commands keyed by agent name |

**Cross-validation rules**:
- Each target's `agents` list entries must exist in the top-level `agents` list
- Each key in `test_commands` must match an agent `name` from the `agents` list
- Agent `os` should be compatible with target `os` when mapped together

## State Tracking (Runtime)

Test phases share state via a module-scoped dictionary keyed by `(agent_name, target_name)`:

| Key | Type | Set By | Used By |
|-----|------|--------|---------|
| payload_uuid | str | payload generation phase | payload download, cleanup |
| payload_bytes | bytes | payload download phase | payload upload |
| new_callback_id | int | callback verification phase | command execution, cleanup |
| phase_results | dict[str, bool] | each phase | dependency checking |

This state is not persisted — it exists only for the duration of a test run.
