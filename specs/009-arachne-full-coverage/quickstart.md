# Quickstart: Arachne Full Command Coverage

## What Changed

Fixed parameter mismatches in 3 Arachne commands (download, upload, execute_assembly), corrected platform restriction descriptions for 2 commands (cd, execute_assembly), and added agent version metadata.

## File Modified

`src/mythicmcp/plugins/builtin/arachne.yaml` — the only file changed.

## Verify

1. Start the MCP server and confirm Arachne plugin loads with 8 commands
2. Test download: `arachne_download(callback_id=X, file_path="/etc/hostname")`
3. Test upload: First `core_upload_file(...)` to get file_id, then `arachne_upload(callback_id=X, remote_path="/tmp/test.txt", file=file_id)`
4. Test execute_assembly (ASPX only): First `core_upload_file(...)`, then `arachne_execute_assembly(callback_id=X, file=file_id, arguments="-group=system")`

## No Code Changes Required

This feature only modifies YAML configuration. No Python code changes needed — the YAML loader and executor already support the corrected parameter patterns (proven by Apollo's 78-command YAML config).
