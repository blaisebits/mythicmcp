# Contract: YAML Metadata Schema

**Date**: 2026-02-14
**Feature**: 007-apollo-full-coverage

## Change to YamlConfigModel

Add `metadata` as an explicit optional field:

```python
class YamlConfigModel(BaseModel):
    agent: AgentConfigModel
    commands: list[CommandConfigModel]
    metadata: dict[str, Any] | None = None  # NEW

    model_config = {"extra": "allow"}
```

The `warn_extra_fields` validator continues to warn on truly unrecognized keys. Since `metadata` is now a declared field, it won't appear in `model_extra`.

## Metadata Convention

```yaml
metadata:
  agent_version: "2.4.8"
  mythic_version: "3.4.6+"
```

No validation on metadata contents — it's informational. The loader reads it but doesn't act on it. Future features may use metadata fields.

## Impact on Existing Configs

- `apollo.yaml` — gains metadata section
- `arachne.yaml` — optionally gains metadata section (not required)
- External plugins — metadata is optional, no breaking change
- Tests — existing YAML parsing tests unaffected (metadata is optional)
