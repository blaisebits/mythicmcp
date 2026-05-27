# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-05-27

Initial public release.

### Added

- Core Mythic MCP tools for:
  - connection and operation context
  - callbacks, tasks, and task output
  - file upload/download workflows
  - payload creation, validation, and download
  - C2 profile discovery and saved C2 instances
- Generic callback-command workflow:
  - `core_list_callback_commands`
  - `core_get_callback_command`
  - `core_execute_callback_command`
- Bundled typed agent toolsets for Apollo, Poseidon, and Arachne
- YAML-driven plugin system for defining additional agent tools
- Docker Codex harness and integration helpers for fresh-session MCP testing

### Notes

- `callback_id` is the canonical callback identifier for follow-on work.
- `display_id` is returned for Mythic UI/operator correlation.
