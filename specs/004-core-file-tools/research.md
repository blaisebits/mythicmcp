# Research: Core File Management Tools

**Feature**: 004-core-file-tools
**Date**: 2026-02-01

## Mythic Python API Analysis

### 1. File Upload: `register_file()`

**Location**: `mythic/mythic.py:1621-1636`

**Signature**:
```python
async def register_file(
    mythic: mythic_classes.Mythic,
    filename: str,
    contents: bytes
) -> str:
```

**Behavior**:
- Uploads file as multipart form data to `/api/v1.4/task_upload_file_webhook`
- Returns `agent_file_id` (UUID string) on success
- Returns `None` on failure (logs error)

**Decision**: Wrap directly. Convert base64 input to bytes before calling.

**Rationale**: Simple wrapper pattern matches existing tools. Base64→bytes conversion handles MCP transport requirement.

**Alternatives Considered**:
- Streaming upload: Not needed for <50MB files, adds complexity
- File path input: Would require server filesystem access, violates MCP isolation

---

### 2. File Download: `download_file()` / `download_file_chunked()`

**Location**: `mythic/mythic.py:1639-1658`

**Signatures**:
```python
async def download_file(mythic: mythic_classes.Mythic, file_uuid: str) -> bytes

async def download_file_chunked(
    mythic: mythic_classes.Mythic,
    file_uuid: str,
    chunk_size: int = 512000
) -> AsyncGenerator
```

**Behavior**:
- `download_file`: Downloads entire file as bytes from `/direct/download/{file_uuid}`
- `download_file_chunked`: Returns async generator for streaming large files

**Decision**: Use `download_file()` for simplicity. Return base64-encoded content.

**Rationale**:
- For files up to 50MB, loading into memory is acceptable
- Chunked download would require MCP streaming support (not standard)
- Base64 encoding roughly 33% overhead is acceptable for this use case

**Alternatives Considered**:
- Chunked download with pagination: MCP doesn't support streaming responses natively
- Return file reference instead of content: Would require additional download step

---

### 3. List Downloaded Files: `get_all_downloaded_files()`

**Location**: `mythic/mythic.py:1661-1690`

**Signature**:
```python
async def get_all_downloaded_files(
    mythic: mythic_classes.Mythic,
    custom_return_attributes: str = None,
    batch_size: int = 100
) -> AsyncGenerator
```

**Behavior**:
- Queries `filemeta` table with `is_download_from_agent: true, complete: true`
- Returns batches of file metadata as async generator
- Default attributes from `file_data_fragment` include:
  - `agent_file_id`, `filename_utf8`, `full_remote_path_utf8`
  - `host`, `complete`, `deleted`, `timestamp`
  - `md5`, `sha1`, `comment`
  - `operator.username`, `task.id`, `task.command.cmd`

**Decision**: Collect all batches into single list response. Use custom attributes for efficiency.

**Rationale**:
- Operations typically have <1000 files (per SC-003)
- Single response simplifies MCP tool interface
- Custom attributes avoid unnecessary data transfer

**Custom Attributes Selection**:
```graphql
id
agent_file_id
filename_utf8
full_remote_path_utf8
host
complete
timestamp
md5
sha1
comment
task {
    id
    callback {
        id
        display_id
    }
}
```

---

### 4. List Uploaded Files: `get_all_uploaded_files()`

**Location**: `mythic/mythic.py:1786-1815`

**Signature**:
```python
async def get_all_uploaded_files(
    mythic: mythic_classes.Mythic,
    custom_return_attributes: str = None,
    batch_size: int = 10
) -> AsyncGenerator
```

**Behavior**:
- Queries `filemeta` with filters: `is_screenshot: false, is_download_from_agent: false, is_payload: false`
- Returns batches of file metadata as async generator
- Same default attributes as downloaded files

**Decision**: Same pattern as downloaded files. Custom attributes for relevant metadata.

**Custom Attributes Selection**:
```graphql
id
agent_file_id
filename_utf8
complete
timestamp
comment
operator {
    username
}
```

---

## Base64 Encoding Strategy

**Decision**: Use Python's `base64.b64encode()` / `base64.b64decode()` for all file content.

**Rationale**:
- Standard Python library, no additional dependencies
- MCP JSON transport requires string encoding for binary data
- 33% size overhead acceptable for files up to 50MB (~67MB encoded)

**Implementation Pattern**:
```python
import base64

# Upload: decode base64 input to bytes
content_bytes = base64.b64decode(content_base64)

# Download: encode bytes to base64 output
content_base64 = base64.b64encode(content_bytes).decode('ascii')
```

---

## Error Handling Strategy

**Decision**: Follow existing MythicMCP patterns with typed error responses.

| Error Condition | Response Type | Error Message |
|-----------------|---------------|---------------|
| File not found | `FileNotFoundError` | "File with UUID {uuid} not found" |
| Upload failed | `FileUploadError` | "Failed to upload file: {reason}" |
| Invalid base64 | `ValueError` | "Invalid base64-encoded content" |
| No operation set | `NoCurrentOperationError` | "No current operation set" |
| Connection error | `MythicConnectionError` | "Failed to connect to Mythic server" |

---

## File Size Considerations

**Upload Limits**:
- SC-001 targets 5s for <10MB files
- Mythic Python API uses multipart form upload
- Network latency dominates for small files

**Download Limits**:
- SC-002 targets 50MB without timeout
- MCP response size should handle ~67MB (50MB + base64 overhead)
- Consider adding size check before download

**Decision**: No explicit size limits in implementation. Let Mythic server enforce its limits. Document recommended max file sizes in tool descriptions.

---

## Callback/Task Association

Downloaded files are associated with the task that downloaded them. The Mythic API includes:
- `task.id` - Task ID that initiated the download
- `task.callback.id` - Callback that executed the task

**Decision**: Include callback display_id in downloaded files response for operator context.

**Implementation**: Use custom GraphQL attributes to fetch callback info:
```graphql
task {
    id
    callback {
        id
        display_id
    }
}
```
