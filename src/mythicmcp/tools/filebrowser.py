"""File browser tools for MythicMCP.

Provides tools for querying Mythic's file browser (mythictree table),
which stores directory listings produced by agent commands like poseidon ls:
- core_get_file_browser_by_task: Entries created by a specific task
- core_list_file_browser: Entries for a host, optionally filtered by path
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

from mythicmcp.models import (
    FileBrowserEntry,
    GetFileBrowserByTaskResponse,
    ListFileBrowserResponse,
)

if TYPE_CHECKING:
    from mythic import mythic_classes

    from mythicmcp.connection import MythicContext

logger = logging.getLogger(__name__)


class FileBrowserError(Exception):
    """Base exception for file browser operations."""

    pass


class NoOperationSetError(FileBrowserError):
    """Raised when no current operation is set in Mythic."""

    pass


# Fields matching the Mythic UI's fileObjData fragment on the mythictree table.
# File metadata (size, permissions, times) lives inside the `metadata` JSON column.
_MYTHICTREE_FIELDS = """
    id
    name_text
    full_path_text
    parent_path_text
    host
    can_have_children
    has_children
    success
    deleted
    comment
    timestamp
    tree_type
    metadata
    task_id
"""

_FILE_BROWSER_BY_TASK_QUERY = f"""
query GetFileBrowserByTask($task_display_id: Int!) {{
    mythictree(
        where: {{
            task: {{display_id: {{_eq: $task_display_id}}}},
            tree_type: {{_eq: "file"}}
        }},
        order_by: {{id: asc}}
    ) {{
        {_MYTHICTREE_FIELDS}
    }}
}}
"""

_FILE_BROWSER_BY_HOST_QUERY = f"""
query ListFileBrowserByHost($host: String!) {{
    mythictree(
        where: {{
            host: {{_eq: $host}},
            tree_type: {{_eq: "file"}},
            deleted: {{_eq: false}}
        }},
        order_by: {{id: asc}}
    ) {{
        {_MYTHICTREE_FIELDS}
    }}
}}
"""

_FILE_BROWSER_BY_HOST_PATH_QUERY = f"""
query ListFileBrowserByHostPath($host: String!, $path: String!) {{
    mythictree(
        where: {{
            host: {{_eq: $host}},
            parent_path_text: {{_eq: $path}},
            tree_type: {{_eq: "file"}},
            deleted: {{_eq: false}}
        }},
        order_by: {{id: asc}}
    ) {{
        {_MYTHICTREE_FIELDS}
    }}
}}
"""


def _parse_file_browser_entry(data: dict) -> FileBrowserEntry:
    """Parse raw mythictree data into FileBrowserEntry model.

    File metadata (size, permissions, access/modify times) is extracted
    from the `metadata` JSON column.

    Args:
        data: Raw dict from GraphQL response.

    Returns:
        FileBrowserEntry model.
    """
    metadata = data.get("metadata") or {}
    if isinstance(metadata, str):
        import json

        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    return FileBrowserEntry(
        id=data.get("id", 0),
        name=data.get("name_text", "") or "",
        full_path=data.get("full_path_text", "") or "",
        parent_path=data.get("parent_path_text", "") or "",
        host=data.get("host", "") or "",
        is_file=not bool(data.get("can_have_children", False)),
        size=metadata.get("size"),
        permissions=_extract_permissions(metadata.get("permissions")),
        access_time=metadata.get("access_time"),
        modify_time=metadata.get("modify_time"),
        comment=data.get("comment", "") or "",
        success=data.get("success"),
        timestamp=data.get("timestamp"),
    )


def _extract_permissions(perms: object) -> str:
    """Normalize permissions from metadata to a display string.

    Permissions may be a simple string or a structured object depending
    on the agent. Returns a string representation in either case.
    """
    if perms is None:
        return ""
    if isinstance(perms, str):
        return perms
    if isinstance(perms, dict):
        import json

        return json.dumps(perms)
    return str(perms)


async def get_file_browser_by_task(
    mythic_instance: mythic_classes.Mythic, task_display_id: int
) -> GetFileBrowserByTaskResponse:
    """Fetch file browser entries created by a specific task.

    Args:
        mythic_instance: Authenticated Mythic instance.
        task_display_id: Display ID of the task (e.g. an ls command).

    Returns:
        GetFileBrowserByTaskResponse with entries.

    Raises:
        NoOperationSetError: If no current operation is set.
        FileBrowserError: For other errors.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    try:
        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=_FILE_BROWSER_BY_TASK_QUERY,
            variables={"task_display_id": task_display_id},
        )

        raw_entries = (
            result.get("mythictree", []) if isinstance(result, dict) else []
        )
        entries = [_parse_file_browser_entry(e) for e in raw_entries]

        return GetFileBrowserByTaskResponse(
            task_display_id=task_display_id,
            entries=entries,
            count=len(entries),
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise FileBrowserError(
            f"Failed to retrieve file browser entries: {e}"
        ) from e


async def list_file_browser(
    mythic_instance: mythic_classes.Mythic,
    host: str,
    path: str | None = None,
) -> ListFileBrowserResponse:
    """List file browser entries for a host, optionally filtered by path.

    Args:
        mythic_instance: Authenticated Mythic instance.
        host: Target hostname to query.
        path: Optional parent path to filter entries (e.g. "/etc").
              When provided, returns entries whose parent_path matches exactly.

    Returns:
        ListFileBrowserResponse with matching entries.

    Raises:
        NoOperationSetError: If no current operation is set.
        FileBrowserError: For other errors.
    """
    from mythic import mythic

    if not mythic_instance.current_operation_id:
        raise NoOperationSetError(
            "No current operation set. Run core_list_operations, then core_set_operation."
        )

    try:
        if path is not None:
            query = _FILE_BROWSER_BY_HOST_PATH_QUERY
            variables: dict = {"host": host, "path": path}
        else:
            query = _FILE_BROWSER_BY_HOST_QUERY
            variables = {"host": host}

        result = await mythic.execute_custom_query(
            mythic=mythic_instance,
            query=query,
            variables=variables,
        )

        raw_entries = (
            result.get("mythictree", []) if isinstance(result, dict) else []
        )
        entries = [_parse_file_browser_entry(e) for e in raw_entries]

        return ListFileBrowserResponse(
            host=host,
            path=path,
            entries=entries,
            count=len(entries),
        )

    except Exception as e:
        error_msg = str(e).lower()
        if "operation" in error_msg:
            raise NoOperationSetError(
                "No current operation set. Run core_list_operations, then core_set_operation."
            ) from e
        raise FileBrowserError(
            f"Failed to list file browser entries: {e}"
        ) from e


async def core_get_file_browser_by_task(
    ctx: Context, task_display_id: int
) -> GetFileBrowserByTaskResponse:
    """Retrieve file browser entries created by a specific Mythic task.

    Commands like poseidon_ls store their results in Mythic's file browser
    (mythictree table) rather than as task response text. Use this tool
    to fetch the directory listing produced by such a task.

    Returns file/directory metadata: name, full path, size, permissions,
    access/modify times, and whether each entry is a file or directory.
    Size, permissions, and times are extracted from the metadata JSON column.

    Args:
        task_display_id: The task display ID to fetch results for (required)
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_file_browser_by_task(mythic_ctx.mythic, task_display_id)
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except FileBrowserError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_get_file_browser_by_task")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )


async def core_list_file_browser(
    ctx: Context, host: str, path: str | None = None
) -> ListFileBrowserResponse:
    """List known file browser entries for a host across the current operation.

    Queries Mythic's accumulated file browser data for a given hostname.
    Optionally filter to entries whose parent path matches exactly (e.g.
    path="/etc" returns files directly inside /etc).

    This data is built up over time as agents run directory listing commands.
    It represents a composite view of everything Mythic has observed on that
    host, not just a single ls invocation.

    Args:
        host: Target hostname (required)
        path: Parent path to filter on (optional, e.g. "/etc")
    """
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData

    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_file_browser(mythic_ctx.mythic, host, path)
    except NoOperationSetError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except FileBrowserError as e:
        raise McpError(ErrorData(code=-1, message=str(e)))
    except Exception as e:
        logger.exception("Unexpected error in core_list_file_browser")
        raise McpError(
            ErrorData(code=-1, message=f"Unexpected error: {type(e).__name__}")
        )
