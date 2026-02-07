# Data Model: Core File Management Tools

**Feature**: 004-core-file-tools
**Date**: 2026-02-01

## Pydantic Models

### Request Models

#### UploadFileRequest (implicit via tool parameters)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | `str` | Yes | Name for the file on Mythic server |
| `content` | `str` | Yes | Base64-encoded file content |

#### DownloadFileRequest (implicit via tool parameters)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_uuid` | `str` | Yes | UUID of file to download |

### Response Models

#### UploadFileResponse

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether upload succeeded |
| `file_id` | `str` | UUID of uploaded file (for use in tasking) |
| `filename` | `str` | Filename as stored |
| `message` | `str` | Status message |
| `retrieved_at` | `datetime` | Timestamp of operation |

#### UploadFileErrorResponse

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Always `False` |
| `error` | `str` | Error message |
| `error_type` | `str` | Error category |
| `retrieved_at` | `datetime` | Timestamp of operation |

#### DownloadFileResponse

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether download succeeded |
| `file_uuid` | `str` | UUID of downloaded file |
| `filename` | `str` | Original filename |
| `content` | `str` | Base64-encoded file content |
| `size_bytes` | `int` | File size in bytes (before encoding) |
| `md5` | `str \| None` | MD5 hash if available |
| `sha1` | `str \| None` | SHA1 hash if available |
| `retrieved_at` | `datetime` | Timestamp of operation |

#### DownloadFileErrorResponse

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Always `False` |
| `error` | `str` | Error message |
| `error_type` | `str` | Error category: `not_found`, `connection_error` |
| `file_uuid` | `str` | Requested UUID |
| `retrieved_at` | `datetime` | Timestamp of operation |

#### DownloadedFileSummary

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Internal Mythic file ID |
| `file_uuid` | `str` | File UUID (agent_file_id) |
| `filename` | `str` | Filename (UTF-8) |
| `full_remote_path` | `str` | Full path on target system |
| `host` | `str` | Source hostname |
| `size_bytes` | `int \| None` | File size if known |
| `complete` | `bool` | Whether download completed |
| `timestamp` | `datetime` | Download timestamp |
| `md5` | `str \| None` | MD5 hash |
| `sha1` | `str \| None` | SHA1 hash |
| `comment` | `str` | File comment |
| `callback_id` | `int \| None` | Source callback ID |
| `callback_display_id` | `int \| None` | Source callback display number |
| `task_id` | `int \| None` | Task that initiated download |

#### ListDownloadedFilesResponse

| Field | Type | Description |
|-------|------|-------------|
| `files` | `list[DownloadedFileSummary]` | List of downloaded files |
| `count` | `int` | Total number of files |
| `retrieved_at` | `datetime` | Timestamp of query |

#### UploadedFileSummary

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Internal Mythic file ID |
| `file_id` | `str` | File UUID (agent_file_id) for tasking |
| `filename` | `str` | Filename (UTF-8) |
| `complete` | `bool` | Whether upload completed |
| `timestamp` | `datetime` | Upload timestamp |
| `comment` | `str` | File comment |
| `operator` | `str` | Username who uploaded |

#### ListUploadedFilesResponse

| Field | Type | Description |
|-------|------|-------------|
| `files` | `list[UploadedFileSummary]` | List of uploaded files |
| `count` | `int` | Total number of files |
| `retrieved_at` | `datetime` | Timestamp of query |

## Entity Relationships

```
┌─────────────────┐     ┌─────────────────┐
│  UploadedFile   │     │ DownloadedFile  │
├─────────────────┤     ├─────────────────┤
│ file_id (UUID)  │     │ file_uuid (UUID)│
│ filename        │     │ filename        │
│ timestamp       │     │ timestamp       │
│ operator        │     │ host            │
│ comment         │     │ full_remote_path│
│                 │     │ callback_id     │
│                 │     │ task_id         │
│                 │     │ md5, sha1       │
└─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────────────────────────────┐
│           Mythic filemeta table         │
│  (unified storage, differentiated by    │
│   is_download_from_agent flag)          │
└─────────────────────────────────────────┘
```

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| `filename` | Non-empty string | "Filename cannot be empty" |
| `content` | Valid base64 | "Invalid base64-encoded content" |
| `file_uuid` | UUID format | "Invalid file UUID format" |

## State Transitions

Files in Mythic have a `complete` status:
- **Uploading**: `complete=False` during transfer
- **Complete**: `complete=True` when fully uploaded
- **Deleted**: `deleted=True` when marked for deletion

The MCP tools only expose completed files (filter: `complete=True`).
