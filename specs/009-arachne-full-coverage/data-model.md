# Data Model: Arachne Full Command Coverage

## Entities

### Arachne YAML Config

Single YAML file defining all Arachne commands. No new entities; this feature modifies existing field values.

**Fields modified**:

| Command | Field | Old Value | New Value |
|---------|-------|-----------|-----------|
| download | parameter name | `path` | `file_path` |
| upload | parameter name | `file_contents` | `file` |
| upload | parameter description | "Base64-encoded file contents" | "file_id from core_upload_file" |
| execute_assembly | parameter 1 name | `assembly_name` | `file` |
| execute_assembly | parameter 1 description | "Name of registered .NET assembly" | "file_id from core_upload_file containing .NET assembly" |
| execute_assembly | parameter 2 name | `assembly_arguments` | `arguments` |
| cd | description | generic | includes "(Windows only)" |
| execute_assembly | description | generic | includes "(Windows/ASPX only)" |

**New fields**:

| Location | Field | Value |
|----------|-------|-------|
| agent-level | `metadata.agent_version` | `"0.0.4"` |

## State Transitions

N/A — YAML config is static, loaded at startup.

## Validation Rules

- All parameter names must match Mythic agent source exactly
- `type: string` required for all file_id parameters
- `required: true` for `file` and `file_path` parameters
- `default: ""` for optional `arguments` parameter
