# MCP Tool Contracts: Core File Management Tools

**Feature**: 004-core-file-tools
**Date**: 2026-02-01

## Tool Definitions

### 1. core_upload_file

**Description**: Upload a file to the Mythic server for use in agent tasking operations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `filename` | `string` | Yes | Name for the file on Mythic server |
| `content` | `string` | Yes | Base64-encoded file content |

**Returns**: `UploadFileResponse` or `UploadFileErrorResponse`

**Example Request**:
```json
{
  "filename": "mimikatz.exe",
  "content": "TVqQAAMAAAAEAAAA//8AALgAAAA..."
}
```

**Example Success Response**:
```json
{
  "success": true,
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "mimikatz.exe",
  "message": "File uploaded successfully",
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

**Example Error Response**:
```json
{
  "success": false,
  "error": "Failed to upload file: connection timeout",
  "error_type": "connection_error",
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

---

### 2. core_download_file

**Description**: Download a file from the Mythic server by its UUID.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_uuid` | `string` | Yes | UUID of the file to download |

**Returns**: `DownloadFileResponse` or `DownloadFileErrorResponse`

**Example Request**:
```json
{
  "file_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Example Success Response**:
```json
{
  "success": true,
  "file_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "passwords.txt",
  "content": "cGFzc3dvcmRzIGZpbGUgY29udGVudA==",
  "size_bytes": 24,
  "md5": "098f6bcd4621d373cade4e832627b4f6",
  "sha1": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

**Example Error Response**:
```json
{
  "success": false,
  "error": "File not found",
  "error_type": "not_found",
  "file_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

---

### 3. core_list_downloaded_files

**Description**: List all files downloaded from agents in the current operation.

**Parameters**: None (uses current operation context)

**Returns**: `ListDownloadedFilesResponse`

**Example Response**:
```json
{
  "files": [
    {
      "id": 42,
      "file_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "filename": "passwords.txt",
      "full_remote_path": "C:\\Users\\admin\\Documents\\passwords.txt",
      "host": "WORKSTATION01",
      "size_bytes": 1024,
      "complete": true,
      "timestamp": "2026-02-01T11:30:00Z",
      "md5": "098f6bcd4621d373cade4e832627b4f6",
      "sha1": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
      "comment": "Credential file",
      "callback_id": 5,
      "callback_display_id": 3,
      "task_id": 127
    }
  ],
  "count": 1,
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

---

### 4. core_list_uploaded_files

**Description**: List all files uploaded to the Mythic server in the current operation.

**Parameters**: None (uses current operation context)

**Returns**: `ListUploadedFilesResponse`

**Example Response**:
```json
{
  "files": [
    {
      "id": 15,
      "file_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "filename": "mimikatz.exe",
      "complete": true,
      "timestamp": "2026-02-01T10:00:00Z",
      "comment": "Credential dumping tool",
      "operator": "operator1"
    }
  ],
  "count": 1,
  "retrieved_at": "2026-02-01T12:00:00Z"
}
```

---

## Error Types

| Error Type | Description | HTTP Equivalent |
|------------|-------------|-----------------|
| `not_found` | File UUID does not exist | 404 |
| `connection_error` | Cannot reach Mythic server | 503 |
| `invalid_input` | Invalid base64 or parameters | 400 |
| `no_operation` | No current operation set | 400 |
| `permission_denied` | Access denied to file | 403 |

## Usage Workflow

```
1. Upload file for tasking:
   core_upload_file(filename, content) → file_id

2. Use file_id in agent task:
   apollo_upload(callback_id, file=file_id, path="/tmp/tool.exe")

3. After agent downloads file from target:
   core_list_downloaded_files() → list with file_uuid

4. Retrieve downloaded file content:
   core_download_file(file_uuid) → base64 content
```
