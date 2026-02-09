# Quickstart: Integration Testing Pipeline

**Feature**: 005-integration-testing
**Date**: 2026-02-08

## Prerequisites

- Python 3.10+
- A running Mythic server (v3.3+) with Apollo and/or Arachne agents installed
- Two target systems with pre-existing callbacks:
  - Debian Linux system with an active callback
  - Windows 11 system with an active callback
- `uv` installed for dependency management

## Setup

### 1. Install dependencies

```bash
uv sync --dev
```

PyYAML is added as a dev dependency for YAML config parsing.

### 2. Create test configuration

Copy the sample configuration and fill in your environment details:

```bash
cp tests/integration/config.sample.yaml tests/integration/config.yaml
```

Edit `tests/integration/config.yaml` with your:
- Mythic server URL and API token
- Target system hostnames and pre-existing callback IDs
- C2 profile parameters matching your Mythic setup

### 3. Verify Mythic connectivity

```bash
uv run pytest tests/integration/test_connection.py -v
```

## Running Tests

### Run all integration tests

```bash
uv run pytest tests/integration/ -v -m integration
```

### Run a specific phase

```bash
# Config validation only
uv run pytest tests/unit/test_integration_config.py -v

# Payload generation only
uv run pytest tests/integration/test_payload_generation.py -v -m integration

# Full pipeline for a specific target
uv run pytest tests/integration/ -v -m integration -k "windows"
```

### Override config path

```bash
MYTHICMCP_TEST_CONFIG=/path/to/custom/config.yaml uv run pytest tests/integration/ -v -m integration
```

## Configuration Reference

See `tests/integration/config.sample.yaml` for the full schema with inline comments. Key sections:

- `mythic`: Server URL and credentials
- `timeouts`: Default timeouts for each phase
- `agents`: Agent types to build and test
- `targets`: Systems to deploy payloads to (each lists which agents to test)
- `test_commands`: Commands to run per agent type after callback verification

## Test Output

Tests report per-phase, per-agent/target pair:

```
tests/integration/test_payload_generation.py::test_generate_payload[apollo] PASSED
tests/integration/test_payload_generation.py::test_download_payload[apollo] PASSED
tests/integration/test_payload_deployment.py::test_upload_payload[apollo-windows-target] PASSED
tests/integration/test_payload_deployment.py::test_execute_payload[apollo-windows-target] PASSED
tests/integration/test_callback_verification.py::test_verify_callback[apollo-windows-target] PASSED
tests/integration/test_command_execution.py::test_run_command[apollo-windows-target-whoami] PASSED
tests/integration/test_command_execution.py::test_run_command[apollo-windows-target-pwd] PASSED
tests/integration/test_cleanup.py::test_cleanup_payload[apollo-windows-target] PASSED
tests/integration/test_cleanup.py::test_deactivate_callback[apollo-windows-target] PASSED
```

Failed dependency phases cause later phases to show as SKIPPED:

```
tests/integration/test_callback_verification.py::test_verify_callback[arachne-linux-target] FAILED
tests/integration/test_command_execution.py::test_run_command[arachne-linux-target-id] SKIPPED (dependency failed)
```

## Adding a New Agent or Target

Edit `tests/integration/config.yaml` only — no code changes needed:

1. Add agent config under `agents:` with payload type, OS, C2 profile
2. Add target under `targets:` with hostname, callback ID, and agent list
3. Add test commands under `test_commands:` for the new agent
4. Run tests
