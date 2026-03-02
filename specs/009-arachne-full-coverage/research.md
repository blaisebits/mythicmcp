# Research: Arachne Full Command Coverage

## R1: YAML Loader File Parameter Support

**Decision**: File parameters use `type: string` with file_id values from `core_upload_file`. No dedicated file type needed.

**Rationale**: The YAML loader supports 3 types: `string`, `integer`, `boolean`. Apollo's 007 branch already uses `type: string` for all file parameters (upload, register_assembly, powershell_import, etc.) with descriptions referencing `core_upload_file`. This pattern is proven and deployed.

**Alternatives considered**: Adding a `type: file` to the YAML schema — rejected because it would require yaml_loader.py changes and the string-with-file_id pattern already works across Apollo's 78 commands.

## R2: Arachne Parameter Mismatches vs Mythic Agent Source

**Decision**: Three commands need parameter fixes:

| Command | Current YAML | Mythic Agent Source | Fix |
|---------|-------------|-------------------|-----|
| `download` | `path` (string) | `file_path` (string) | Rename param to `file_path` |
| `upload` | `remote_path` + `file_contents` (base64) | `remote_path` + `file` (File) | Replace `file_contents` with `file` (file_id string) |
| `execute_assembly` | `assembly_name` + `assembly_arguments` | `file` (File) + `arguments` | Replace both params with `file` (file_id) + `arguments` |

**Rationale**: Verified against Arachne agent source files in `refs/agents/arachne/Payload_Type/arachne/arachne/agent_functions/`. Parameter names must match exactly what Mythic expects or tasks fail silently.

**Alternatives considered**: Keeping `file_contents` with base64 and adding a converter — rejected because Mythic's task system expects file_id references, not raw content.

## R3: Per-Command Platform Restrictions

**Decision**: Use description text only. The YAML schema does not support per-command `supported_os` overrides.

**Rationale**: The yaml_loader.py only supports agent-level `supported_os`. Adding per-command restrictions would require schema and loader changes that are out of scope. Apollo's 007 branch uses the same approach — description-only platform notes. The `cd` and `execute_assembly` descriptions will note Windows-only / ASPX-only.

**Alternatives considered**: Adding `supported_os` to CommandConfigModel — deferred to a future feature. Would benefit all plugins but is unnecessary for correctness.

## R4: file_ids Array in Task Execution

**Decision**: Not an issue for this feature. Existing executor passes parameters dict to `mythic.issue_task()` without explicit `file_ids` array. Apollo's 007 branch uses this exact pattern for all file commands.

**Rationale**: The `execute_task()` function in executor.py calls `mythic.issue_task()` with `parameters=parameters or {}`. Apollo's file-based commands (upload, register_assembly, etc.) work through this same code path. If `file_ids` were strictly required, Apollo would be broken too.

**Alternatives considered**: Adding `file_ids` extraction to executor — deferred as a cross-cutting concern that would be a separate feature.

## R5: Arachne Command Completeness

**Decision**: All 8 user-taskable commands are already in the YAML. No new commands to add.

**Rationale**: Arachne has 9 total commands: shell, pwd, ls, cd, rm, download, upload, execute_assembly, checkin. `checkin` is internal/automatic (system info gathering on initial connection). All 8 user-taskable commands are present; only parameter fixes and metadata are needed.
