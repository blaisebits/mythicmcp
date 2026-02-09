# Research: Integration Testing Pipeline

**Feature**: 005-integration-testing
**Date**: 2026-02-08

## R1: Mythic Payload Generation API

**Decision**: Use `mythic.create_payload()` with `return_on_complete=True` for synchronous payload builds.

**Rationale**: The `create_payload()` function in the mythic Python library (v0.2.10+) accepts `payload_type_name`, `operating_system`, `c2_profiles`, `build_parameters`, and `filename`. Setting `return_on_complete=True` blocks until the build finishes, which is appropriate for sequential test phases. The returned dict includes `uuid`, `build_phase`, and `build_message` for validation.

**Alternatives considered**:
- `create_payload()` with `return_on_complete=False` + `waitfor_payload_complete()`: More control but unnecessary complexity for testing — the synchronous wrapper handles timeouts already.
- Direct GraphQL mutations: Lower-level, harder to maintain, and duplicates what the library provides.

## R2: Payload Download Mechanism

**Decision**: Use `mythic.download_payload(mythic_instance, payload_uuid)` which returns raw bytes.

**Rationale**: This function fetches payload metadata then calls `download_file()` internally. Returns raw binary content that can be validated (non-empty, correct size) and then uploaded to targets via `mythic.register_file()`.

**Alternatives considered**:
- `mythic.download_file()` directly: Requires knowing the `agent_file_id` from the payload metadata. `download_payload()` handles this lookup automatically.

## R3: Callback Deactivation (Cleanup)

**Decision**: Use `mythic.update_callback(callback_display_id, active=False)` to deactivate callbacks after testing.

**Rationale**: The mythic Python library has no `remove_callback` or `exit_callback` function. The only way to deactivate a callback is `update_callback()` with `active=False`. This marks the callback as inactive in the Mythic UI but does not remove it from the database. This is sufficient for test cleanup — inactive callbacks don't appear in active callback lists.

**Alternatives considered**:
- Issuing an "exit" command to the agent via `issue_task()`: Would cleanly terminate the agent process but requires the callback to be responsive. Using `update_callback(active=False)` is more reliable for cleanup since it works even if the agent has crashed.
- Both approaches combined: Issue exit command first (best-effort), then mark inactive via API. Adds complexity for minimal benefit in a test context.

## R4: File Removal from Target Systems

**Decision**: Use existing plugin tools (e.g., `shell` command with OS-appropriate delete) via `mythic.issue_task()` on the pre-existing callback to remove uploaded payloads.

**Rationale**: Arachne has a dedicated `rm` command. Apollo can use `shell` with `del` (Windows) or `rm` (if running on Linux). The cleanup phase uses the pre-existing callback (not the new one being tested) to delete the payload file from the target. This requires the pre-existing callback to still be active during cleanup.

**Alternatives considered**:
- Using the new callback to delete its own payload: Circular — we'd be using the callback we want to deactivate to clean up. Also, the new callback may not have the same file system access.
- Leaving files on disk: Rejected per clarification — full cleanup required.

## R5: Test Phase Dependencies in Pytest

**Decision**: Use pytest fixtures with `request` and module-scoped state to share phase results across tests. Use `pytest.skip()` when a dependency phase fails.

**Rationale**: Pytest doesn't have native test-dependency support, but the pattern of using module-level state (or session-scoped fixtures) to track phase results is well-established. Each test phase checks whether its predecessor succeeded and calls `pytest.skip("dependency phase failed")` if not. Test ordering is ensured by file ordering and pytest's default collection order (alphabetical within modules, declaration order within files).

**Alternatives considered**:
- `pytest-dependency` plugin: Adds external dependency for a simple feature. The skip-on-failure pattern is straightforward enough without it.
- Single monolithic test: Rejected per clarification — separate phases provide better failure diagnostics.
- Pytest fixtures with `autouse` and `xfail`: Doesn't provide clear skip semantics.

## R6: YAML Configuration Schema

**Decision**: Use Pydantic models for YAML configuration validation. Load with PyYAML, validate with Pydantic `model_validate()`.

**Rationale**: The project already uses Pydantic extensively for data models. Using Pydantic for YAML config validation provides type safety, clear error messages, and field-level defaults. PyYAML is a lightweight dependency (already transitive via many packages).

**Alternatives considered**:
- JSON Schema validation: Requires additional tooling (jsonschema package). Less Pythonic, harder to maintain alongside code.
- Manual validation: Error-prone, doesn't provide automatic type coercion or clear validation messages.
- Dataclasses with manual validation: Loses Pydantic's rich validation, error formatting, and optional field handling.

## R7: Callback Polling Strategy

**Decision**: Poll `mythic.get_all_active_callbacks()` at 5-second intervals up to the configured timeout (default 120s). Match on hostname and agent type.

**Rationale**: The mythic library provides `get_all_active_callbacks()` which returns all active callbacks with hostname, agent type, and other metadata. Polling at 5-second intervals balances responsiveness with API load. The 120-second default timeout accommodates typical payload startup times including process injection and C2 negotiation.

**Alternatives considered**:
- GraphQL subscription for new callbacks: More efficient (event-driven) but significantly more complex. The polling approach is simpler and adequate for test scenarios with low callback volumes.
- Shorter polling interval (1s): Unnecessary API load for a test that runs infrequently.
- Longer default timeout: 120s is already generous. Operators can override via YAML config.

## R8: Test Result Reporting

**Decision**: Rely on pytest's built-in reporting with `-v` flag. Each phase is a separate test function, so pass/fail/skip is reported per phase per agent/target pair.

**Rationale**: Pytest already provides clear per-test reporting with timing, failure details, and skip reasons. Parametrized tests (by agent/target pair) produce output like `test_payload_generation[apollo-windows11] PASSED`. No custom reporting framework is needed.

**Alternatives considered**:
- Custom HTML/JSON report: Over-engineering for this use case. Can be added later with `pytest-html` if needed.
- Custom logging framework: Duplicates what pytest already does.
