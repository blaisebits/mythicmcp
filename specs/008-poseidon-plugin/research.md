# Research: Poseidon Agent Built-in Plugin

## R1: Poseidon Command Inventory

**Decision**: Target all 76 Poseidon 2.2.8 commands grouped into 13 categories.

**Rationale**: Full coverage matches the Apollo plugin approach (78 commands) and prevents operators from needing the Mythic UI fallback.

**Categories and command counts**:
- Shell & Command Execution (5): shell, pty, run, jxa, ssh
- File Operations (11): ls, cat, cd, pwd, head, tail, mkdir, rm, cp, mv, download, upload, download_bulk, triagedirectory
- Process Management (4): ps, kill, jobkill, jobs
- Environment Variables (6): getenv, setenv, unsetenv, curl_env_get, curl_env_set, curl_env_clear
- User & Credentials (5): getuser, sudo, test_password, sshauth, prompt
- Network Operations (5): ifconfig, portscan, curl, socks, rpfwd
- Persistence (2): persist_launchd, persist_loginitem (macOS only)
- Code Injection (5): libinject, execute_library, jsimport, jsimport_call, xpc_load
- Logging & Data Collection (4): keylog, screencapture, clipboard, clipboard_monitor
- System Information (8): drives, lsopen, list_entitlements, tcc_check, keys, config, print_c2, print_p2p
- Configuration & Control (7): sleep, update_c2, link_tcp, unlink_tcp, link_webshell, unlink_webshell, exit, caffeinate
- XPC (macOS) (7): xpc_send, xpc_service, xpc_submit, xpc_procinfo, xpc_manageruid, xpc_unload, xpc_load
- Shell Config (2): shell_config, chmod

**Alternatives considered**: Subset coverage — rejected because partial coverage was explicitly rejected in the spec.

## R2: Parameter Type Mapping

**Decision**: Map all Poseidon parameters to the 3 types supported by the YAML loader: string, integer, boolean.

**Rationale**: The existing YAML loader (`yaml_loader.py`) only supports `string`, `integer`, and `boolean` types (line 32). Poseidon commands using arrays (portscan hosts/ports, curl headers) or file references will use `string` type with format guidance in the description field.

**Specific mappings**:
- Array params (hosts, ports, headers, args) → `string` with description: "Comma-separated list" or "JSON array string"
- File params (file_id) → `string` with description referencing `core_upload_file`
- Choose-one params (curl method) → `string` with `choices` field
- Base64-encoded content (JXA code, curl body, xpc_send data) → `string` with description noting base64 encoding

**Alternatives considered**: Extending the YAML loader to support array/file types — rejected per FR-005 (no loader changes).

## R3: macOS-Only Command Handling

**Decision**: Document macOS-only restriction in tool descriptions; do not enforce at MCP layer.

**Rationale**: Per spec assumption, Mythic server validates OS compatibility. Adding MCP-layer enforcement would require loader changes. Descriptions will include "(macOS only)" prefix for affected commands.

**Affected commands**: jxa, persist_launchd, persist_loginitem, libinject, execute_library, list_entitlements, tcc_check, xpc_* (7 commands), keylog (partial — works differently on Linux).

## R4: Parameter Groups

**Decision**: Flatten parameter groups into optional parameters.

**Rationale**: Mythic's parameter groups (e.g., upload's "New File" vs "Existing File") are a UI concept. The API accepts flat parameters — unused group params are simply omitted. This matches Apollo's upload command pattern.

**Affected commands**: upload (file_id vs existing), ssh (password vs private_key), execute_library (new file vs existing).

## R5: Unit Test Strategy

**Decision**: Add Poseidon-specific tests to existing `test_yaml_loader.py`.

**Rationale**: Apollo and Arachne tests are already in this file. Follow the same pattern: load the YAML, verify agent metadata, verify command count, spot-check specific commands.

**Alternatives considered**: Separate test file — rejected to maintain consistency with existing test organization.
