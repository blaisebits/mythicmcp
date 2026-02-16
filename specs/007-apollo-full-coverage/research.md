# Research: Apollo Full Command Coverage

**Date**: 2026-02-14
**Feature**: 007-apollo-full-coverage

## R1: Apollo Agent Version

**Decision**: Target Apollo version 2.4.8 (Mythic 3.4.6+, container mythic-container==0.6.6)
**Rationale**: This is the version present in refs/agents/Apollo/. Version string found in config.json and container version markers.
**Alternatives**: None — single reference source.

## R2: Total Command Count

**Decision**: 62 active commands (golden_ticket is entirely commented out in source, excluded)
**Rationale**: Exhaustive audit of all .py files in `refs/agents/Apollo/Payload_Type/apollo/apollo/mythic/agent_functions/`. Each file defines one command class.
**Alternatives**: Including golden_ticket (commented out) — rejected, non-functional code.

## R3: Commands Requiring Special Handling

**Decision**: All 62 commands will be defined in YAML. Commands with Mythic-special parameter types (ConnectionInfo, LinkInfo, Payload, Credential_JSON) or script_only orchestrators will use `string` parameters with descriptive text. The YAML config calls `execute_with_validation` which submits the task to Mythic — Mythic handles the server-side logic regardless of how parameters are submitted.

**Commands with non-standard parameter types** (14 total):
- `link` — ConnectionInfo → string (JSON connection info)
- `unlink` — LinkInfo → string (JSON link info)
- `spawn` — Payload → string (payload template UUID)
- `inject` — Payload template → string
- `socks` — script_only but params are standard (port, action)
- `jump_wmi` — Payload option → string
- `jump_psexec` — Payload option → string
- `load` — dynamic choices → string
- `make_token` — Credential_JSON option → use standard params (username, password, netOnly)
- `pth` — multi-group (NTLM/AES128/AES256/Credential) → flatten to string params
- `ticket_store_add` — Credential_JSON option → string (base64ticket)
- `ticket_cache_add` — Credential_JSON option → string (base64ticket)
- `mimikatz` — alias wrapping execute_pe → string (commands)
- `dcsync` — alias wrapping execute_pe → string params
- `printspoofer` — alias wrapping execute_pe → string (command line)

**Rationale**: The YAML-generated handler calls `execute_with_validation()` which passes parameters to Mythic's `issue_task_and_waitfor_task_output()`. Mythic processes the parameters server-side. For commands with parameter groups, we expose the most common/useful group's parameters. For alias commands, we expose the user-facing parameters — Mythic handles the alias expansion.

**Alternatives**: Exclude complex commands — rejected per clarification (include all).

## R4: Parameter Type Mapping

**Decision**: Map all Mythic parameter types to the 3 supported YAML types:

| Mythic Type | YAML Type | Notes |
|------------|-----------|-------|
| String | string | Direct mapping |
| Number | integer | Direct mapping |
| Boolean | boolean | Direct mapping |
| File | string | Description notes "file_id from core_upload_file" |
| ChooseOne | string | Add `choices` list in YAML |
| Array | string | Description notes JSON array format |
| ConnectionInfo | string | Description notes expected JSON format |
| LinkInfo | string | Description notes expected JSON format |
| Credential_JSON | string | Description notes expected format |
| TypedArray | string | Description notes JSON format |

**Rationale**: The YAML schema supports string/integer/boolean. All complex types serialize to strings. File parameters reference file_ids from the core_upload_file tool.

## R5: Metadata Field Implementation

**Decision**: Add `metadata` as an explicit optional field on `YamlConfigModel` (dict type, default None). This prevents the existing `warn_extra_fields` validator from logging a warning.
**Rationale**: Cleaner than filtering in the warning logic. Makes metadata a first-class concept.
**Alternatives**: Filter "metadata" in warn_extra_fields — rejected, less explicit.

## R6: Commands with Raw Command Line Parameters

Several commands accept raw command line strings instead of formal parameters:
- `net_dclist` — domain name as raw arg
- `net_localgroup` — computer name as raw arg
- `set_injection_technique` — technique name as raw arg
- `printspoofer` — command line as raw arg

**Decision**: Define these with a single `command` (or appropriately named) string parameter. The handler passes it through to Mythic which handles parsing.
**Rationale**: Consistent with how `shell` works — a single string parameter containing the full command.

## R7: Parameter Groups

Commands like `sc`, `pth`, `make_token`, `shinject` use Mythic "parameter groups" — different sets of parameters for different modes of operation. The YAML schema doesn't support parameter groups.

**Decision**: Flatten to the most commonly used parameter group. Include all parameters from that group, plus any shared parameters. Document the group choice in the command description.
- `sc` — expose action as string (query/start/stop/create/delete) + all possible params (service, computer, display_name, binpath), make action-specific ones optional
- `pth` — expose NTLM group (domain, user, ntlm, run) as most common use case
- `make_token` — expose Default group (username, password, netOnly)
- `shinject` — expose Default group (pid, shellcode as file_id)

**Rationale**: Parameter groups are a Mythic UI concept. The task JSON just includes whichever parameters are provided. Mythic resolves which group to use based on which params are present.
