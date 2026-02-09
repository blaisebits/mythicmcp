# Test Helper Contracts: Integration Testing Pipeline

**Feature**: 005-integration-testing
**Date**: 2026-02-08

## Overview

These contracts define the internal helper functions used by integration tests. They are not MCP tools — they are async Python functions in the test infrastructure that wrap Mythic API calls for test use.

---

## config_loader

### `load_integration_config(path: str | None = None) -> IntegrationTestConfig`

Loads and validates the YAML configuration file.

**Parameters**:
- `path`: Optional path override. Defaults to `tests/integration/config.yaml`. Can be overridden by `MYTHICMCP_TEST_CONFIG` environment variable.

**Returns**: Validated `IntegrationTestConfig` Pydantic model.

**Errors**:
- `FileNotFoundError`: Config file does not exist at path.
- `ValidationError` (Pydantic): Config file has invalid structure or missing required fields.

**Behavior**:
1. Check `MYTHICMCP_TEST_CONFIG` env var for path override
2. Fall back to provided `path` argument
3. Fall back to `tests/integration/config.yaml` relative to repo root
4. Load YAML with `yaml.safe_load()`
5. Validate with `IntegrationTestConfig.model_validate()`
6. Run cross-validation (agent references, OS compatibility)
7. Return validated config

---

## payload_helpers

### `async generate_payload(mythic_instance, agent_config: AgentConfig, timeout: int = 300) -> str`

Generates a payload on the Mythic server.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `agent_config`: Agent configuration from YAML
- `timeout`: Build timeout in seconds

**Returns**: Payload UUID string.

**Errors**:
- `TimeoutError`: Build did not complete within timeout
- `PayloadBuildError`: Build completed with error status

**Behavior**:
1. Call `mythic.create_payload()` with agent config parameters and `return_on_complete=True`
2. Check `build_phase` == "success"
3. Return `uuid`

---

### `async download_payload(mythic_instance, payload_uuid: str) -> bytes`

Downloads a built payload from the Mythic server.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `payload_uuid`: UUID from `generate_payload()`

**Returns**: Raw payload bytes.

**Errors**:
- `PayloadDownloadError`: Download failed or returned empty content

**Behavior**:
1. Call `mythic.download_payload(mythic_instance, payload_uuid)`
2. Validate result is non-empty bytes
3. Return bytes

---

## deployment_helpers

### `async upload_payload_to_target(mythic_instance, payload_bytes: bytes, target: TargetConfig, agent_config: AgentConfig) -> str`

Uploads a payload to a target system via an existing callback.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `payload_bytes`: Raw payload content
- `target`: Target system configuration
- `agent_config`: Agent config (for filename)

**Returns**: Mythic file_id of the uploaded file.

**Behavior**:
1. Register file with Mythic via `mythic.register_file()`
2. Issue upload task to pre-existing callback (`target.callback_id`)
3. Wait for upload task completion
4. Return file_id

---

### `async execute_payload_on_target(mythic_instance, target: TargetConfig, agent_config: AgentConfig) -> None`

Executes an uploaded payload on the target system.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `target`: Target system config (includes upload_path and callback_id)
- `agent_config`: Agent config (for OS-appropriate execution command)

**Behavior**:
1. Determine execution command based on target OS:
   - Windows: `shell` with `target.upload_path` (starts process)
   - Linux: `shell` with `chmod +x && target.upload_path &` (background execution)
2. Issue task to pre-existing callback
3. Wait for task acknowledgment (not completion — payload runs independently)

---

## callback_helpers

### `async wait_for_callback(mythic_instance, hostname: str, agent_type: str, timeout: int = 120, poll_interval: int = 5, baseline_ids: set[int] | None = None) -> int`

Polls for a new callback matching the expected criteria.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `hostname`: Expected hostname in callback
- `agent_type`: Expected agent/payload type name
- `timeout`: Maximum wait time in seconds
- `poll_interval`: Seconds between polls
- `baseline_ids`: Set of callback IDs that existed before payload execution (to filter pre-existing callbacks)

**Returns**: Callback display_id of the new callback.

**Errors**:
- `TimeoutError`: No matching callback appeared within timeout

**Behavior**:
1. Record start time
2. Loop until timeout:
   a. Call `mythic.get_all_active_callbacks()`
   b. Filter by hostname match (case-insensitive) and agent type match
   c. Exclude any IDs in `baseline_ids`
   d. If match found, return its `display_id`
   e. Sleep `poll_interval` seconds
3. Raise `TimeoutError` with expected criteria details

---

### `async get_baseline_callback_ids(mythic_instance) -> set[int]`

Captures current callback IDs before payload execution for filtering.

**Returns**: Set of all current active callback display_ids.

---

## command_helpers

### `async execute_test_command(mythic_instance, callback_id: int, command: TestCommandConfig) -> tuple[bool, str]`

Executes a single test command and validates output.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `callback_id`: Callback to execute on
- `command`: Test command configuration

**Returns**: Tuple of (passed: bool, output: str).

**Behavior**:
1. Call `mythic.issue_task()` with `wait_for_complete=True` and `timeout`
2. Collect output via `mythic.get_all_task_output_by_id()`
3. If `expected_output` is set, first try `re.search(expected_output, output)` for regex matching; if the pattern is invalid regex, fall back to substring containment check
4. Return (match_result, collected_output)

---

## cleanup_helpers

### `async cleanup_payload_on_target(mythic_instance, target: TargetConfig) -> bool`

Removes the uploaded payload file from the target system.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `target`: Target config (includes upload_path and callback_id)

**Returns**: True if cleanup succeeded, False otherwise.

**Behavior** (best-effort):
1. Determine delete command based on target OS:
   - Windows: `shell` with `del /f "upload_path"`
   - Linux: `shell` with `rm -f upload_path`
2. Issue task to pre-existing callback
3. Log warning on failure, return False
4. Return True on success

---

### `async deactivate_callback(mythic_instance, callback_display_id: int) -> bool`

Deactivates a callback created during testing.

**Parameters**:
- `mythic_instance`: Authenticated Mythic connection
- `callback_display_id`: Callback to deactivate

**Returns**: True if deactivation succeeded, False otherwise.

**Behavior** (best-effort):
1. Call `mythic.update_callback(callback_display_id, active=False)`
2. Check response for success
3. Log warning on failure, return False
4. Return True on success
