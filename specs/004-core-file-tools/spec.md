# Feature Specification: Core File Management Tools

**Feature Branch**: `004-core-file-tools`
**Created**: 2026-02-01
**Status**: Draft
**Input**: User description: "Core file management tools for uploading, downloading, and listing files on the Mythic server"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload File for Tasking (Priority: P1)

An operator needs to upload a file (such as a tool, script, or payload) to the Mythic server so it can be used in subsequent agent tasking operations (e.g., pushing the file to a compromised host via an upload command).

**Why this priority**: File upload is the foundational operation that enables file transfer workflows. Without the ability to register files on the Mythic server, operators cannot push files to agents.

**Independent Test**: Can be tested by uploading a test file and verifying a file_id is returned that can be used in tasking.

**Acceptance Scenarios**:

1. **Given** an operator with an active Mythic session, **When** they upload a file with content and filename, **Then** the system returns a unique file_id that can be used for agent tasking
2. **Given** an operator uploading a file, **When** the upload completes successfully, **Then** the file is registered in the current operation and appears in the uploaded files list
3. **Given** an operator uploading a file, **When** the Mythic server is unreachable, **Then** the system returns a clear error message indicating the connection failure

---

### User Story 2 - Download File from Mythic Server (Priority: P1)

An operator needs to retrieve a file that was previously downloaded from a compromised host (via agent download command) or uploaded to Mythic. This allows them to examine collected data, exfiltrated files, or retrieve payloads.

**Why this priority**: Retrieving files is equally critical as uploading. Operators need to access files that agents have collected from target systems.

**Independent Test**: Can be tested by downloading a known file UUID and verifying the file content is returned correctly.

**Acceptance Scenarios**:

1. **Given** a valid file UUID in the current operation, **When** an operator requests to download the file, **Then** the file content is returned as bytes (base64 encoded for MCP transport)
2. **Given** a large file (over 1MB), **When** an operator downloads it, **Then** the system handles the transfer without timeout or memory issues
3. **Given** an invalid or non-existent file UUID, **When** an operator attempts to download, **Then** the system returns a clear error message indicating the file was not found

---

### User Story 3 - List Downloaded Files (Priority: P2)

An operator needs to see all files that have been downloaded from compromised hosts during the current operation. This provides visibility into what data has been collected.

**Why this priority**: Listing downloaded files is essential for operational awareness but depends on download operations having occurred first.

**Independent Test**: Can be tested by listing files and verifying the response includes expected metadata fields.

**Acceptance Scenarios**:

1. **Given** an active operation with downloaded files, **When** an operator requests the list of downloaded files, **Then** the system returns file metadata including filename, size, source callback, and timestamp
2. **Given** an operation with no downloaded files, **When** an operator requests the list, **Then** the system returns an empty list without error
3. **Given** an operation with many files (up to 1000), **When** an operator requests the list, **Then** the system returns results within 2 seconds (per SC-003)

---

### User Story 4 - List Uploaded Files (Priority: P2)

An operator needs to see all files that have been uploaded to the Mythic server for the current operation. This helps track what tools and payloads are available for tasking.

**Why this priority**: Similar to downloaded files, listing uploads provides operational visibility and helps operators find file_ids for use in tasking.

**Independent Test**: Can be tested by listing uploaded files and verifying the response includes expected metadata.

**Acceptance Scenarios**:

1. **Given** an active operation with uploaded files, **When** an operator requests the list of uploaded files, **Then** the system returns file metadata including filename, size, upload timestamp, and file_id
2. **Given** an operation with no uploaded files, **When** an operator requests the list, **Then** the system returns an empty list without error

---

### Edge Cases

- What happens when a file upload fails midway due to network interruption?
- How does the system handle attempting to download a file from a different operation?
- What happens when file content is empty (zero bytes)?
- How are binary files vs text files handled during transfer?
- What happens when the file has special characters in the filename?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `core_upload_file` tool that accepts file content and filename, registers the file with Mythic, and returns the file_id
- **FR-002**: System MUST provide a `core_download_file` tool that accepts a file UUID and returns the file content
- **FR-003**: System MUST provide a `core_list_downloaded_files` tool that returns metadata for all files downloaded from agents in the current operation
- **FR-004**: System MUST provide a `core_list_uploaded_files` tool that returns metadata for all files uploaded to the Mythic server in the current operation
- **FR-005**: File content for upload MUST be provided as base64-encoded data to ensure safe transport of binary content
- **FR-006**: Downloaded file content MUST be returned as base64-encoded data to ensure safe transport of binary content
- **FR-007**: All file operations MUST respect the current operation context
- **FR-008**: File metadata listings MUST include: filename, file size, timestamp, and unique identifier (UUID or file_id)
- **FR-009**: Downloaded files listing MUST include the source callback identifier when available
- **FR-010**: System MUST provide clear error messages when file operations fail (not found, permission denied, connection error)

### Key Entities

- **UploadedFile**: A file registered with Mythic for use in agent tasking. Key attributes: file_id, filename, size, upload timestamp, operation_id
- **DownloadedFile**: A file retrieved from a compromised host via an agent. Key attributes: file_uuid, filename, size, download timestamp, source_callback, complete status, operation_id

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can upload a file and receive a valid file_id within 5 seconds for files under 10MB
- **SC-002**: Operators can download files up to 50MB without timeout or errors
- **SC-003**: File listings return results within 2 seconds for operations with up to 1000 files
- **SC-004**: All four core file tools are discoverable via `core_list_plugins` or tool enumeration
- **SC-005**: 100% of file operations provide actionable error messages when they fail

## Assumptions

- The Mythic Python API (`mythic` package) provides the underlying `register_file()`, `download_file()`, `get_all_downloaded_files()`, and `get_all_uploaded_files()` functions
- Base64 encoding is acceptable for file content transport through MCP
- Files are scoped to the current operation context (set via `core_set_operation`)
- Large file handling follows the existing patterns in the Mythic Python API (chunked transfer where needed)
- The MCP server has sufficient memory to handle reasonable file sizes (the Mythic Python API handles streaming for very large files)

## Out of Scope

- Payload generation and management (separate feature)
- File browser / remote filesystem tree operations (separate feature)
- Credential management (separate feature)
- Agent-specific upload commands (already exist in Apollo/Arachne plugins)
- File synchronization or bulk operations
- Real-time file subscriptions
