# Config Schema & Plugin Architecture Checklist: YAML-Driven Agent Plugin Configuration

**Purpose**: Validate that YAML schema requirements and plugin architecture requirements are complete, clear, consistent, and measurable
**Created**: 2026-02-15
**Feature**: [spec.md](../spec.md)
**Focus**: Config schema design + Plugin architecture (coexistence, loader, registry)
**Depth**: Standard
**Audience**: Reviewer (PR)

## Requirement Completeness — Schema Definition

- [ ] CHK001 Are all supported YAML top-level keys enumerated (currently `agent` and `commands`)? [Completeness, Spec §FR-003/§FR-004]
- [ ] CHK002 Is the behavior for YAML syntax errors (malformed YAML, not just invalid structure) specified? [Gap]
- [ ] CHK003 Are requirements for empty string values defined (e.g., `description: ""`)? [Edge Case, Data Model §CommandDef]
- [ ] CHK004 Is the allowed character set for `agent.name` fully specified, including what happens with uppercase or special characters? [Clarity, Data Model §AgentConfig]
- [ ] CHK005 Are requirements defined for maximum file size or maximum number of commands per config file? [Gap, Scale]
- [ ] CHK006 Is the behavior for `mythic_command` being empty or whitespace-only specified? [Edge Case, Data Model §CommandDef]
- [ ] CHK007 Are encoding requirements specified for YAML files (e.g., UTF-8 only)? [Gap]

## Requirement Completeness — Parameter System

- [ ] CHK008 Are requirements for conflicting constraints specified (e.g., `min` > `max`, or `default` outside `min`/`max` range)? [Edge Case, Data Model §ParameterDef]
- [ ] CHK009 Is the interaction between `required: true` and `default` being provided explicitly defined? [Clarity, Spec §FR-005]
- [ ] CHK010 Are requirements for empty `choices` lists specified (e.g., `choices: []`)? [Edge Case, Data Model §ParameterDef]
- [ ] CHK011 Is behavior defined for `choices` containing duplicate values? [Edge Case, Data Model §ParameterDef]
- [ ] CHK012 Are requirements specified for boolean parameter default values in YAML (e.g., `true` vs `True` vs `yes`)? [Clarity, Data Model §ParameterDef]
- [ ] CHK013 Is the complete reserved parameter name list defined beyond `callback_id` and `timeout`? [Completeness, Spec §FR-005, Edge Cases §reserved names]
- [ ] CHK014 Are requirements for parameter ordering (does order in YAML affect tool schema order?) specified? [Gap]

## Requirement Clarity — Validation & Error Reporting

- [ ] CHK015 Is "specific, actionable error" quantified with what fields must be present in error messages? [Clarity, Spec §FR-007]
- [ ] CHK016 Are validation error severity levels defined (error vs warning) with clear criteria for each? [Clarity, Spec §US3 Acceptance Scenario 4]
- [ ] CHK017 Is the distinction between "skip plugin" and "reject config" explicitly defined for each error category? [Consistency, Spec §FR-007]
- [ ] CHK018 Are requirements for logging levels of validation messages specified (info/warning/error)? [Gap]
- [ ] CHK019 Is the validation error contract (file, agent, errors array) referenced from the spec or only in the contract doc? [Traceability, Contract §Validation Error]

## Requirement Consistency — Cross-Document

- [ ] CHK020 Does the spec's edge case for "zero commands" conflict with the data model's "at least one entry" requirement for commands? [Conflict, Spec §Edge Cases vs Data Model §AgentConfig]
- [ ] CHK021 Is the `agent.name` character set consistent between spec (not specified), data model (alphanumeric + hyphens), and contract (alphanumeric + hyphens)? [Consistency]
- [ ] CHK022 Is `command.name` character set consistent — data model says "underscores" while `agent.name` says "hyphens"? [Consistency, Data Model §AgentConfig vs §CommandDef]
- [ ] CHK023 Are the reserved word lists consistent between the data model (ctx, context, self) and the spec edge cases (ctx only)? [Consistency, Spec §Edge Cases vs Data Model §CommandDef]

## Requirement Completeness — Plugin Architecture

- [ ] CHK024 Is the loading order between YAML-based and code-based plugins explicitly specified in the spec (not just research.md)? [Gap, Spec §FR-012]
- [ ] CHK025 Are requirements for conflict resolution when YAML and code-based plugins define the same agent name specified in the spec? [Gap, Spec §FR-012]
- [ ] CHK026 Is the external plugins directory YAML discovery requirement documented (not just code-based external plugins)? [Completeness, Spec §FR-002]
- [ ] CHK027 Are requirements for the `MYTHICMCP_PLUGINS_DIR` environment variable supporting YAML files specified? [Gap, Spec §FR-002]
- [ ] CHK028 Is the file extension discovery requirement explicit (`.yaml` and `.yml`)? [Gap]
- [ ] CHK029 Are requirements for plugin load order determinism specified (alphabetical, modification time, etc.)? [Gap, Edge Cases §duplicate agent name]

## Requirement Completeness — Registry & Introspection

- [ ] CHK030 Are requirements defined for distinguishing config-based vs code-based plugins in `core_list_plugins` output? [Gap, Spec §FR-009]
- [ ] CHK031 Are requirements for reporting config file path in plugin metadata specified? [Gap, Spec §FR-009]
- [ ] CHK032 Is the PluginLoadError interface specified for config validation failures (currently only defined for code plugin failures)? [Completeness, Spec §FR-007]

## Acceptance Criteria Quality

- [ ] CHK033 Can SC-003 ("100% of structural errors") be objectively measured without an enumerated list of structural error categories? [Measurability, Spec §SC-003]
- [ ] CHK034 Can SC-004 ("30% code reduction") be measured objectively, and is the measurement scope defined (Apollo only, or entire plugin system)? [Measurability, Spec §SC-004]
- [ ] CHK035 Are acceptance scenarios defined for the handler auto-generation step (FR-006), not just for end-to-end tool behavior? [Coverage, Spec §FR-006]

## Edge Case Coverage

- [ ] CHK036 Are requirements defined for what happens when a YAML file has valid YAML but is completely empty (no `agent` or `commands` keys)? [Edge Case, Gap]
- [ ] CHK037 Are requirements defined for a YAML file that contains only comments? [Edge Case, Gap]
- [ ] CHK038 Are requirements for file permission errors (unreadable YAML file) specified? [Edge Case, Gap]
- [ ] CHK039 Is behavior defined when the same command name appears in both a YAML config and a code-based plugin for different agents? [Edge Case, Spec §FR-008]

## Notes

- Items reference spec sections as `[Spec §FR-XXX]`, data model sections as `[Data Model §Entity]`, and contract sections as `[Contract §Section]`
- `[Gap]` markers indicate requirements that may need to be added to the spec
- `[Conflict]` markers indicate potential inconsistencies between documents
- Focus areas: Config schema design + Plugin architecture (per user request)
- Migration fidelity was explicitly excluded from this checklist
