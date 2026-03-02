# Config, Schema & Architecture Checklist: Poseidon Agent Built-in Plugin

**Purpose**: Validate requirements quality across config correctness, cross-plugin consistency, and test coverage for the Poseidon YAML plugin.
**Created**: 2026-02-28
**Feature**: [spec.md](../spec.md)
**Depth**: Standard (~30 items)

## Requirement Completeness

- [ ] CHK001 - Are all 76 Poseidon 2.2.8 commands enumerated and accounted for in the spec or research? [Completeness, Spec §FR-001]
- [ ] CHK002 - Is the complete list of macOS-only commands documented so implementers know which descriptions need the "(macOS only)" prefix? [Completeness, Spec §FR-004, Research §R3]
- [ ] CHK003 - Are all commands with parameter groups (upload, ssh, execute_library) identified with their flattened parameter strategy? [Completeness, Research §R4]
- [ ] CHK004 - Are all commands using file_id parameters identified so they can reference `core_upload_file` in descriptions? [Completeness, Spec §FR-006]
- [ ] CHK005 - Are all commands with array-type parameters identified with their expected format (comma-separated, JSON array)? [Completeness, Spec §FR-007]
- [ ] CHK006 - Are all commands with choose-one semantics identified so `choices` fields can be applied? [Completeness, Spec §FR-010]

## Requirement Clarity

- [ ] CHK007 - Is "all Poseidon 2.2.8 commands" precisely defined with a concrete count, or does the spec rely on the vague "~76"? [Clarity, Spec §FR-001, SC-001]
- [ ] CHK008 - Is the format for array parameters unambiguous — does each array-param command specify whether to use comma-separated or JSON array format? [Clarity, Spec §FR-007]
- [ ] CHK009 - Are base64-encoding requirements for specific parameters (JXA code, curl body, xpc_send data) clearly specified per-command? [Clarity, Research §R2]
- [ ] CHK010 - Is the distinction between commands that take a raw string parameter vs structured dict parameters clear for each command? [Clarity, Spec §FR-002]
- [ ] CHK011 - Are timeout defaults specified per-command or per-category, and is the rationale for non-default timeouts documented? [Clarity, Spec §FR-002]

## Cross-Plugin Consistency

- [ ] CHK012 - Are naming conventions for Poseidon tool descriptions consistent with Apollo/Arachne patterns (e.g., "Execute X on a Poseidon callback")? [Consistency]
- [ ] CHK013 - Do shared command names (shell, ls, cat, pwd, cd, mkdir, rm, cp, mv, download, upload, ps, kill, jobs, ifconfig, sleep, exit, socks, rpfwd) use consistent parameter naming across Poseidon, Apollo, and Arachne? [Consistency]
- [ ] CHK014 - Is the `metadata` section structured consistently with Apollo (agent_version, mythic_version fields)? [Consistency]
- [ ] CHK015 - Are YAML section comment headers (category groupings) following the same style as apollo.yaml? [Consistency]
- [ ] CHK016 - Do file operation commands (upload, download) follow the same parameter patterns as their Apollo equivalents? [Consistency]

## Acceptance Criteria Quality

- [ ] CHK017 - Is SC-001 ("70+ tools") precise enough to be objectively measured, or should it specify the exact expected count? [Measurability, Spec §SC-001]
- [ ] CHK018 - Is SC-005 ("same result as Mythic UI") measurable without defining specific commands to compare? [Measurability, Spec §SC-005]
- [ ] CHK019 - Are unit test assertions defined with specific expected values (agent name, OS list, command count) rather than vague "loads correctly"? [Measurability, Spec §FR-008]

## Scenario Coverage

- [ ] CHK020 - Are requirements defined for what happens when a Poseidon command name collides with an existing tool from another plugin? [Coverage, Gap]
- [ ] CHK021 - Are requirements specified for commands that behave differently on macOS vs Linux (e.g., keylog, shell)? [Coverage, Edge Case, Research §R3]
- [ ] CHK022 - Are requirements defined for commands with optional parameters where all parameters are omitted? [Coverage, Edge Case]
- [ ] CHK023 - Are requirements specified for handling Poseidon commands that require elevated privileges (libinject, keylog on Linux)? [Coverage, Gap]

## Edge Case Coverage

- [ ] CHK024 - Is the behavior defined when a command's `mythic_command` name differs from its YAML `name` (if any Poseidon commands need this)? [Edge Case, Spec §FR-002]
- [ ] CHK025 - Are duplicate command names within the YAML addressed by existing loader validation, and is this assumption documented? [Edge Case, Assumption]
- [ ] CHK026 - Is the behavior defined for parameter groups where the user provides conflicting parameters (e.g., both password and private_key for ssh)? [Edge Case, Research §R4]

## Test Coverage Requirements

- [ ] CHK027 - Are specific representative commands identified for unit test spot-checks, or is the selection left to the implementer? [Completeness, Spec §FR-008]
- [ ] CHK028 - Are integration test commands specified for both macOS and Linux targets, or only one OS? [Coverage, Spec §FR-009]
- [ ] CHK029 - Is the expected integration test command set representative of all 13 command categories? [Coverage, Spec §FR-009]
- [ ] CHK030 - Are unit tests required to verify that macOS-only commands include the OS restriction in their descriptions? [Coverage, Gap]

## Dependencies & Assumptions

- [ ] CHK031 - Is the assumption that no YAML loader changes are needed validated against all Poseidon parameter types? [Assumption, Spec §FR-005]
- [ ] CHK032 - Is the Poseidon agent version (2.2.8) pinned to a specific reference commit or release tag? [Assumption, Spec §Assumptions]
- [ ] CHK033 - Is the assumption that Mythic server handles OS validation documented with a reference to the relevant Mythic behavior? [Assumption, Spec §Assumptions]

## Notes

- Focus areas: Config/schema correctness, cross-plugin consistency, test coverage
- Depth: Standard
- Audience: Reviewer (PR)
- This checklist validates requirements quality, not implementation correctness
