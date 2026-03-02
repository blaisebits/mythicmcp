# Checklist: Config Completeness & Schema Architecture

**Purpose**: Validate that command definitions, parameter mappings, metadata requirements, and schema design decisions are complete, clear, and consistent across spec/plan/research artifacts.
**Created**: 2026-02-14
**Feature**: [spec.md](../spec.md)
**Focus**: Combined config completeness + schema architecture
**Depth**: Standard
**Audience**: Reviewer (PR)

## Requirement Completeness

- [ ] CHK001 - Is the total command count (62) explicitly enumerated with a full list of command names? [Completeness, Research §R2]
- [ ] CHK002 - Are all 14 commands with non-standard parameter types individually documented with their mapping rationale? [Completeness, Research §R3]
- [ ] CHK003 - Are timeout defaults specified per-command or per-category with clear assignment rules? [Completeness, Spec §Assumptions]
- [ ] CHK004 - Are the 4 raw-command-line commands (net_dclist, net_localgroup, set_injection_technique, printspoofer) documented with their parameter name choice? [Completeness, Research §R6]
- [ ] CHK005 - Is the exclusion of golden_ticket (commented-out code) documented with rationale? [Completeness, Research §R2]

## Requirement Clarity

- [ ] CHK006 - Is "100% coverage" defined as exactly 62 commands, or could it change if the reference is re-audited? [Clarity, Spec §FR-001]
- [ ] CHK007 - Is the `metadata` field's type (`dict[str, Any] | None`) and validation behavior (none) explicitly specified? [Clarity, Research §R5]
- [ ] CHK008 - For File-type parameters mapped to string, is the expected input format (file_id vs base64 content) consistently defined? [Clarity, Research §R4]
- [ ] CHK009 - Is the `choices` YAML field usage specified for ChooseOne parameters (e.g., reg_query hive, socks action)? [Clarity, Research §R4]
- [ ] CHK010 - For parameter group flattening (sc, pth, make_token, shinject), is the chosen group explicitly named and justified? [Clarity, Research §R7]

## Requirement Consistency

- [ ] CHK011 - Are parameter names consistent between the research audit and the data model inventory? [Consistency, Research vs Data Model]
- [ ] CHK012 - Is the command categorization consistent between research audit (15 categories) and data-model.md? [Consistency]
- [ ] CHK013 - Are timeout values consistent with existing apollo.yaml patterns (60s quick, 120s file/assembly)? [Consistency, Spec §Assumptions]
- [ ] CHK014 - Is the `description` field requirement for commands consistent — must it state what Mythic operation is performed per Constitution §IV? [Consistency, Constitution §IV]

## Acceptance Criteria Quality

- [ ] CHK015 - Is SC-001 ("tool count equals total") testable without hardcoding 62, or does it require a reference count? [Measurability, Spec §SC-001]
- [ ] CHK016 - Is SC-002 ("parameter schemas match reference") measurable — how would a test verify "correct types, required flags, defaults"? [Measurability, Spec §SC-002]
- [ ] CHK017 - Is SC-004 ("no unrecognized key warnings") testable with a specific log-capture mechanism? [Measurability, Spec §SC-004]

## Scenario Coverage

- [ ] CHK018 - Are requirements defined for commands that are `script_only` in Mythic (inject, socks, jump_wmi, jump_psexec) — will they work via execute_with_validation? [Coverage, Research §R3]
- [ ] CHK019 - Are requirements defined for alias commands (mimikatz, dcsync, pth, printspoofer) — will Mythic expand the alias when called via task API? [Coverage, Research §R3]
- [ ] CHK020 - Are requirements specified for commands that dynamically populate choices (execute_assembly, execute_pe, execute_coff) — should YAML omit the `choices` field? [Coverage, Gap]
- [ ] CHK021 - Is the behavior defined for commands with `needs_admin: True` (getsystem, jump_wmi, jump_psexec) when called from a non-elevated callback? [Coverage, Gap]

## Edge Case Coverage

- [ ] CHK022 - Are requirements defined for the `sleep` command's special default value of -1 (meaning "no change")? [Edge Case, Research audit]
- [ ] CHK023 - Is behavior specified for `ppid` parameter validation (must be divisible by 4 per reference)? [Edge Case, Research audit]
- [ ] CHK024 - Are requirements defined for `execute_coff`'s internal `timeout` parameter (distinct from YAML timeout) that defaults to 30? [Edge Case, Research audit]
- [ ] CHK025 - Is the handling of optional parameters with empty-string defaults (e.g., ls path=".", reg_query key="") documented? [Edge Case, Gap]

## Schema Architecture

- [ ] CHK026 - Is the decision to add `metadata` as a declared Pydantic field (vs filtering in warn_extra_fields) justified with tradeoffs? [Architecture, Research §R5]
- [ ] CHK027 - Are the contents of the `metadata` dict left intentionally unvalidated, and is this decision documented? [Architecture, Contracts §yaml-metadata-schema]
- [ ] CHK028 - Is the impact on arachne.yaml documented — is metadata optional for all plugins or required for builtins? [Architecture, Contracts §yaml-metadata-schema]
- [ ] CHK029 - Is the parameter group flattening approach documented as a schema limitation with potential future enhancement path? [Architecture, Research §R7]

## Dependencies & Assumptions

- [ ] CHK030 - Is the assumption that `execute_with_validation` handles all parameter passing (including non-standard types) validated against the executor source? [Assumption, Research §R3]
- [ ] CHK031 - Is the assumption that Mythic resolves parameter groups from provided params (not from an explicit group name) validated? [Assumption, Research §R7]
- [ ] CHK032 - Is the Apollo version (2.4.8) derivation method documented — where exactly was this string found? [Assumption, Research §R1]
- [ ] CHK033 - Are test file changes (tool count assertion update) listed as explicit deliverables? [Dependency, Quickstart]

## Notes

- 33 items covering both config completeness and schema architecture
- Focus: requirement quality for a data-heavy YAML expansion + minimal code change
- Key risk areas: parameter group flattening correctness, script_only/alias command compatibility
