"""File management tools for MythicMCP.

Provides tools for managing files on the Mythic server:
- core_upload_file: Upload a file to Mythic for agent tasking
- core_download_file: Download a file from Mythic by UUID
- core_list_downloaded_files: List files downloaded from agents
- core_list_uploaded_files: List files uploaded to Mythic
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    DownloadedFileSummary,
    DownloadFileErrorResponse,
    DownloadFileResponse,
    ListDownloadedFilesResponse,
    ListUploadedFilesResponse,
    UploadedFileSummary,
    UploadFileErrorResponse,
    UploadFileResponse,
)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


# --- Exception Classes ---


class FileError(Exception):
    """Base exception for file operations."""

    pass


class FileNotFoundError(FileError):
    """Raised when a file is not found by UUID."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        super().__init__(f"File with UUID {uuid} not found in current operation")


class FileUploadError(FileError):
    """Raised when file upload fails."""

    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to upload file '{filename}': {reason}")


class InvalidBase64Error(FileError):
    """Raised when base64 content is invalid."""

    def __init__(self, details: str):
        self.details = details
        super().__init__(f"Invalid base64-encoded content: {details}")


class NoOperationError(FileError):
    """Raised when no current operation is set."""

    def __init__(self):
        super().__init__("No current operation set. Use core_set_operation first.")


class ConnectionError(FileError):
    """Raised when connection to Mythic server fails."""

    def __init__(self, details: str):
        self.details = details
        super().__init__(f"Failed to connect to Mythic server: {details}")


# --- Helper Functions ---


def _decode_base64_content(content: str) -> bytes:
    """Decode base64-encoded content to bytes.

    Args:
        content: Base64-encoded string

    Returns:
        Decoded bytes

    Raises:
        InvalidBase64Error: If content is not valid base64
    """
    try:
        return base64.b64decode(content, validate=True)
    except Exception as e:
        raise InvalidBase64Error(str(e))


async def upload_file(
    mythic_instance: mythic_classes.Mythic,
    filename: str,
    content_bytes: bytes,
) -> UploadFileResponse:
    """Upload a file to Mythic server.

    Args:
        mythic_instance: Authenticated Mythic instance
        filename: Name for the file on Mythic server
        content_bytes: Raw file content as bytes

    Returns:
        UploadFileResponse with file_id

    Raises:
        NoOperationError: If no current operation is set
        FileUploadError: If upload fails
        ConnectionError: If connection to server fails
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not filename or not filename.strip():
        raise FileUploadError(filename, "Filename cannot be empty")

    try:
        file_id = await mythic.register_file(
            mythic=mythic_instance,
            filename=filename,
            contents=content_bytes,
        )

        if not file_id:
            raise FileUploadError(filename, "Server returned empty file ID")

        return UploadFileResponse(
            success=True,
            file_id=file_id,
            filename=filename,
            message="File uploaded successfully",
        )

    except FileUploadError:
        raise
    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        raise FileUploadError(filename, str(e))


async def _get_file_metadata(
    mythic_instance: mythic_classes.Mythic,
    file_uuid: str,
) -> dict | None:
    """Fetch file metadata from Mythic via GraphQL.

    Args:
        mythic_instance: Authenticated Mythic instance
        file_uuid: UUID of the file to look up

    Returns:
        File metadata dict or None if not found
    """
    from mythic import mythic

    query = """
    query GetFileMetadata($file_uuid: String!) {
        filemeta(where: {agent_file_id: {_eq: $file_uuid}}) {
            id
            agent_file_id
            filename_utf8
            md5
            sha1
            total_chunks
            chunks_received
            complete
        }
    }
    """

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=query,
            variables={"file_uuid": file_uuid},
        )

        files = result.get("filemeta", [])
        if files:
            return files[0]
        return None

    except Exception as e:
        logger.warning(f"Failed to fetch file metadata for {file_uuid}: {e}")
        return None


async def download_file(
    mythic_instance: mythic_classes.Mythic,
    file_uuid: str,
) -> DownloadFileResponse:
    """Download a file from Mythic server by UUID.

    Args:
        mythic_instance: Authenticated Mythic instance
        file_uuid: UUID of the file to download

    Returns:
        DownloadFileResponse with base64-encoded content

    Raises:
        NoOperationError: If no current operation is set
        FileNotFoundError: If file does not exist
        ConnectionError: If connection to server fails
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    if not file_uuid or not file_uuid.strip():
        raise FileNotFoundError(file_uuid)

    # First, get metadata to retrieve filename and hashes
    metadata = await _get_file_metadata(mythic_instance, file_uuid)

    try:
        # Download file content
        content_bytes = await mythic.download_file(
            mythic=mythic_instance,
            file_uuid=file_uuid,
        )

        if content_bytes is None:
            raise FileNotFoundError(file_uuid)

        # Encode content as base64
        content_base64 = base64.b64encode(content_bytes).decode("ascii")

        # Extract metadata fields
        filename = "unknown"
        md5_hash = None
        sha1_hash = None

        if metadata:
            filename = metadata.get("filename_utf8", "unknown") or "unknown"
            md5_hash = metadata.get("md5")
            sha1_hash = metadata.get("sha1")

        return DownloadFileResponse(
            success=True,
            file_uuid=file_uuid,
            filename=filename,
            content=content_base64,
            size_bytes=len(content_bytes),
            md5=md5_hash,
            sha1=sha1_hash,
        )

    except FileNotFoundError:
        raise
    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "404" in error_msg:
            raise FileNotFoundError(file_uuid)
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        # Re-raise as FileNotFoundError for generic failures (likely file doesn't exist)
        raise FileNotFoundError(file_uuid)


# Custom GraphQL attributes for downloaded files with callback info
DOWNLOADED_FILES_ATTRIBUTES = """
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
"""


def _parse_downloaded_file(file_data: dict) -> DownloadedFileSummary:
    """Parse raw file data from Mythic into DownloadedFileSummary model.

    Args:
        file_data: Raw file data from GraphQL response

    Returns:
        DownloadedFileSummary model
    """
    # Extract callback info from nested task structure
    callback_id = None
    callback_display_id = None
    task_id = None

    if task := file_data.get("task"):
        task_id = task.get("id")
        if callback := task.get("callback"):
            callback_id = callback.get("id")
            callback_display_id = callback.get("display_id")

    # Parse timestamp
    timestamp_str = file_data.get("timestamp", "")
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)

    return DownloadedFileSummary(
        id=file_data.get("id", 0),
        file_uuid=file_data.get("agent_file_id", ""),
        filename=file_data.get("filename_utf8", "") or "",
        full_remote_path=file_data.get("full_remote_path_utf8", "") or "",
        host=file_data.get("host", "") or "",
        size_bytes=file_data.get("chunk_size"),  # May be None
        complete=file_data.get("complete", False),
        timestamp=timestamp,
        md5=file_data.get("md5"),
        sha1=file_data.get("sha1"),
        comment=file_data.get("comment", "") or "",
        callback_id=callback_id,
        callback_display_id=callback_display_id,
        task_id=task_id,
    )


async def list_downloaded_files(
    mythic_instance: mythic_classes.Mythic,
) -> ListDownloadedFilesResponse:
    """List all files downloaded from agents in the current operation.

    Args:
        mythic_instance: Authenticated Mythic instance

    Returns:
        ListDownloadedFilesResponse with file list

    Raises:
        NoOperationError: If no current operation is set
        ConnectionError: If connection to server fails
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    try:
        files = []
        async for file_batch in mythic.get_all_downloaded_files(
            mythic=mythic_instance,
            custom_return_attributes=DOWNLOADED_FILES_ATTRIBUTES,
        ):
            for file_data in file_batch:
                files.append(_parse_downloaded_file(file_data))

        return ListDownloadedFilesResponse(
            files=files,
            count=len(files),
        )

    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        if "operation" in error_msg:
            raise NoOperationError()
        raise ConnectionError(f"Failed to list downloaded files: {e}")


# Custom GraphQL attributes for uploaded files
UPLOADED_FILES_ATTRIBUTES = """
id
agent_file_id
filename_utf8
complete
timestamp
comment
operator {
    username
}
"""


def _parse_uploaded_file(file_data: dict) -> UploadedFileSummary:
    """Parse raw file data from Mythic into UploadedFileSummary model.

    Args:
        file_data: Raw file data from GraphQL response

    Returns:
        UploadedFileSummary model
    """
    # Extract operator username from nested structure
    operator = ""
    if operator_data := file_data.get("operator"):
        operator = operator_data.get("username", "") or ""

    # Parse timestamp
    timestamp_str = file_data.get("timestamp", "")
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)

    return UploadedFileSummary(
        id=file_data.get("id", 0),
        file_id=file_data.get("agent_file_id", ""),
        filename=file_data.get("filename_utf8", "") or "",
        complete=file_data.get("complete", False),
        timestamp=timestamp,
        comment=file_data.get("comment", "") or "",
        operator=operator,
    )


async def list_uploaded_files(
    mythic_instance: mythic_classes.Mythic,
) -> ListUploadedFilesResponse:
    """List all files uploaded to Mythic in the current operation.

    Args:
        mythic_instance: Authenticated Mythic instance

    Returns:
        ListUploadedFilesResponse with file list

    Raises:
        NoOperationError: If no current operation is set
        ConnectionError: If connection to server fails
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationError()

    try:
        files = []
        async for file_batch in mythic.get_all_uploaded_files(
            mythic=mythic_instance,
            custom_return_attributes=UPLOADED_FILES_ATTRIBUTES,
        ):
            for file_data in file_batch:
                files.append(_parse_uploaded_file(file_data))

        return ListUploadedFilesResponse(
            files=files,
            count=len(files),
        )

    except NoOperationError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg:
            raise ConnectionError(str(e))
        if "operation" in error_msg:
            raise NoOperationError()
        raise ConnectionError(f"Failed to list uploaded files: {e}")


# --- Tool Entry Points ---


async def core_upload_file(
    ctx: Context,
    filename: str,
    content: str,
) -> UploadFileResponse | UploadFileErrorResponse:
    """Upload a file to the Mythic server for use in agent tasking operations.

    Args:
        filename: Name for the file on Mythic server
        content: Base64-encoded file content

    Returns:
        UploadFileResponse on success, UploadFileErrorResponse on failure
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        # Decode base64 content
        content_bytes = _decode_base64_content(content)

        # Upload file
        return await upload_file(mythic_ctx.mythic, filename, content_bytes)

    except InvalidBase64Error as e:
        return UploadFileErrorResponse(
            error=str(e),
            error_type="invalid_input",
        )
    except NoOperationError as e:
        return UploadFileErrorResponse(
            error=str(e),
            error_type="no_operation",
        )
    except ConnectionError as e:
        return UploadFileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )
    except FileUploadError as e:
        return UploadFileErrorResponse(
            error=str(e),
            error_type="upload_failed",
        )
    except Exception as e:
        logger.exception("Unexpected error in core_upload_file")
        return UploadFileErrorResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}",
            error_type="unexpected_error",
        )


async def core_download_file(
    ctx: Context,
    file_uuid: str,
) -> DownloadFileResponse | DownloadFileErrorResponse:
    """Download a file from the Mythic server by its UUID.

    Args:
        file_uuid: UUID of the file to download

    Returns:
        DownloadFileResponse on success, DownloadFileErrorResponse on failure
    """
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await download_file(mythic_ctx.mythic, file_uuid)

    except FileNotFoundError as e:
        return DownloadFileErrorResponse(
            error=str(e),
            error_type="not_found",
            file_uuid=file_uuid,
        )
    except NoOperationError as e:
        return DownloadFileErrorResponse(
            error=str(e),
            error_type="no_operation",
            file_uuid=file_uuid,
        )
    except ConnectionError as e:
        return DownloadFileErrorResponse(
            error=str(e),
            error_type="connection_error",
            file_uuid=file_uuid,
        )
    except Exception as e:
        logger.exception("Unexpected error in core_download_file")
        return DownloadFileErrorResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}",
            error_type="unexpected_error",
            file_uuid=file_uuid,
        )


async def core_list_downloaded_files(
    ctx: Context,
) -> ListDownloadedFilesResponse:
    """List all files downloaded from agents in the current operation.

    Returns:
        ListDownloadedFilesResponse with file list and count
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_downloaded_files(mythic_ctx.mythic)

    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_downloaded_files")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))


async def core_list_uploaded_files(
    ctx: Context,
) -> ListUploadedFilesResponse:
    """List all files uploaded to the Mythic server in the current operation.

    Returns:
        ListUploadedFilesResponse with file list and count
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_uploaded_files(mythic_ctx.mythic)

    except NoOperationError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except ConnectionError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_uploaded_files")
        raise McpError(ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}"))
