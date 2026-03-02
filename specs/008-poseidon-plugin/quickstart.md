# Quickstart: Poseidon Plugin Implementation

## What to Build

1. **`src/mythicmcp/plugins/builtin/poseidon.yaml`** — YAML plugin config with all ~76 Poseidon 2.2.8 commands
2. **Unit tests** — Add Poseidon tests to `tests/unit/test_yaml_loader.py`
3. **Integration test config** — Add Poseidon section to `tests/integration/config.sample.yaml`

## Implementation Steps

### Step 1: Create poseidon.yaml

Copy the structure from `apollo.yaml`. Change:
- `agent.name` → `poseidon`
- `agent.description` → Poseidon macOS/Linux Golang agent
- `agent.supported_os` → `[macOS, Linux]`
- `metadata.agent_version` → `2.2.8`

Add all commands referencing `refs/agents/poseidon/Payload_Type/poseidon/poseidon/agentfunctions/` for parameter details.

### Step 2: Add Unit Tests

In `tests/unit/test_yaml_loader.py`, add:
```python
class TestPoseidonYamlConfig:
    def test_poseidon_yaml_loads(self):
        # Load poseidon.yaml, assert no errors
    def test_poseidon_command_count(self):
        # Assert >= 70 commands
    def test_poseidon_agent_metadata(self):
        # Assert name, description, supported_os
    def test_poseidon_spot_check_commands(self):
        # Verify shell, curl, portscan have expected params
```

### Step 3: Add Integration Test Config

In `tests/integration/config.sample.yaml`, add a `poseidon:` section under `test_commands:` with representative commands for Linux targets.

### Step 4: Update CLAUDE.md

Update the Available Plugins section to include Poseidon with tool count and description.

## Verification

```bash
# Unit tests
uv run pytest tests/unit/test_yaml_loader.py -v

# All tests
uv run pytest --ignore=tests/integration -x -q
```

## Key References

- Apollo YAML (pattern to follow): `src/mythicmcp/plugins/builtin/apollo.yaml`
- YAML loader (must not change): `src/mythicmcp/plugins/yaml_loader.py`
- Poseidon command definitions: `refs/agents/poseidon/Payload_Type/poseidon/poseidon/agentfunctions/`
