"""C2 profile management tools for MythicMCP.

Provides tools for discovering C2 profiles, querying parameter schemas,
and managing saved C2 profile instances on the Mythic server.
"""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import Context

from mythic import mythic_classes, mythic_utilities

from mythicmcp.connection import MythicContext
from mythicmcp.models import (
    C2InstanceSummary,
    C2ParameterDefinition,
    C2ProfileErrorResponse,
    C2ProfileInfo,
    CreateC2InstanceResponse,
    DeleteC2InstanceResponse,
    GetC2InstanceResponse,
    GetC2ProfileParametersResponse,
    ListC2InstancesResponse,
    ListC2ProfilesResponse,
)

logger = logging.getLogger(__name__)


# --- GraphQL Queries ---

LIST_C2_PROFILES_QUERY = """
query listC2Profiles {
    c2profile {
        name
        description
        is_p2p
        running
        container_running
    }
}
"""

GET_C2_PROFILE_PARAMETERS_QUERY = """
query getC2ProfileParameters($c2_name: String!) {
    c2profileparameters(where: {c2profile: {name: {_eq: $c2_name}}, deleted: {_eq: false}}, order_by: {name: asc}) {
        name
        description
        default_value
        required
        randomize
        parameter_type
        choices
    }
}
"""

GET_C2_PROFILE_ID_QUERY = """
query getC2IdFromName($c2_name: String!) {
    c2profile(where: {name: {_eq: $c2_name}}) {
        id
    }
}
"""

LIST_C2_INSTANCES_QUERY = """
query listC2Instances($c2_profile_id: Int!) {
    c2profileparametersinstance(
        where: {instance_name: {_is_null: false}, c2_profile_id: {_eq: $c2_profile_id}},
        distinct_on: instance_name,
        order_by: {instance_name: asc}
    ) {
        instance_name
    }
}
"""

LIST_ALL_C2_INSTANCES_QUERY = """
query listAllC2Instances {
    c2profileparametersinstance(
        where: {instance_name: {_is_null: false}},
        distinct_on: [instance_name, c2_profile_id],
        order_by: [{instance_name: asc}, {c2_profile_id: asc}]
    ) {
        instance_name
        c2profile {
            name
        }
    }
}
"""

GET_C2_INSTANCE_QUERY = """
query getC2Instance($instance_name: String!, $c2_profile_id: Int!) {
    c2profileparametersinstance(where: {instance_name: {_eq: $instance_name}, c2_profile_id: {_eq: $c2_profile_id}}) {
        c2profileparameter {
            name
            description
            parameter_type
            default_value
            required
            choices
        }
        value
    }
}
"""

DELETE_C2_INSTANCE_MUTATION = """
mutation deleteC2Instance($instance_name: String!, $c2_profile_id: Int!) {
    delete_c2profileparametersinstance(where: {instance_name: {_eq: $instance_name}, c2_profile_id: {_eq: $c2_profile_id}}) {
        affected_rows
    }
}
"""


# --- Business Logic Functions ---


async def _resolve_c2_profile_id(
    mythic_instance: mythic_classes.Mythic,
    c2_profile_name: str,
) -> int:
    """Resolve a C2 profile name to its numeric ID."""
    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=GET_C2_PROFILE_ID_QUERY,
        variables={"c2_name": c2_profile_name},
    )
    profiles = resp.get("c2profile", [])
    if not profiles:
        raise C2ProfileNotFoundError(c2_profile_name)
    return profiles[0]["id"]


async def list_c2_profiles(
    mythic_instance: mythic_classes.Mythic,
) -> ListC2ProfilesResponse:
    """List all available C2 profiles on the Mythic server."""
    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=LIST_C2_PROFILES_QUERY,
    )

    profiles = [
        C2ProfileInfo(
            name=p.get("name", ""),
            description=p.get("description", ""),
            is_p2p=p.get("is_p2p", False),
            running=p.get("running", False),
            container_running=p.get("container_running", False),
        )
        for p in resp.get("c2profile", [])
    ]

    return ListC2ProfilesResponse(
        profiles=profiles,
        total_count=len(profiles),
    )


async def get_c2_profile_parameters(
    mythic_instance: mythic_classes.Mythic,
    c2_profile_name: str,
) -> GetC2ProfileParametersResponse:
    """Get parameter definitions for a specific C2 profile."""
    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=GET_C2_PROFILE_PARAMETERS_QUERY,
        variables={"c2_name": c2_profile_name},
    )

    params_data = resp.get("c2profileparameters", [])
    if not params_data:
        raise C2ProfileNotFoundError(c2_profile_name)

    parameters = [
        C2ParameterDefinition(
            name=p.get("name", ""),
            description=p.get("description", ""),
            default_value=str(p.get("default_value", "")),
            required=p.get("required", False),
            randomize=p.get("randomize", False),
            parameter_type=p.get("parameter_type", "String"),
            choices=p.get("choices", []) or [],
        )
        for p in params_data
    ]

    return GetC2ProfileParametersResponse(
        profile_name=c2_profile_name,
        parameters=parameters,
        parameter_count=len(parameters),
    )


def _coerce_c2_parameter_value(parameter_type: str, value: str) -> object:
    """Coerce saved C2 instance values into the types Mythic expects for payload creation."""
    if value is None:
        return None

    if parameter_type == "Number":
        if value == "":
            return ""
        try:
            return int(value)
        except (TypeError, ValueError):
            try:
                return float(value)
            except (TypeError, ValueError):
                return value

    if parameter_type == "Boolean":
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
        return value

    if parameter_type in {"Dictionary", "Array"}:
        if value == "":
            return {} if parameter_type == "Dictionary" else []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    return value


async def create_c2_instance(
    mythic_instance: mythic_classes.Mythic,
    instance_name: str,
    c2_profile_name: str,
    c2_parameters: dict,
) -> CreateC2InstanceResponse:
    """Create a saved C2 profile instance on the Mythic server."""
    from mythic import mythic as mythic_module

    result = await mythic_module.create_saved_c2_instance(
        mythic=mythic_instance,
        instance_name=instance_name,
        c2_profile_name=c2_profile_name,
        c2_parameters=c2_parameters,
    )

    if result.get("status", "") != "success":
        raise C2InstanceCreateError(result.get("error", "Unknown error"))

    return CreateC2InstanceResponse(
        instance_name=instance_name,
        c2_profile_name=c2_profile_name,
    )


async def list_c2_instances(
    mythic_instance: mythic_classes.Mythic,
) -> ListC2InstancesResponse:
    """List all saved C2 profile instances on the Mythic server."""
    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=LIST_ALL_C2_INSTANCES_QUERY,
    )

    instances = [
        C2InstanceSummary(
            instance_name=i.get("instance_name", ""),
            c2_profile_name=i.get("c2profile", {}).get("name", ""),
        )
        for i in resp.get("c2profileparametersinstance", [])
    ]

    return ListC2InstancesResponse(
        instances=instances,
        total_count=len(instances),
    )


async def get_c2_instance(
    mythic_instance: mythic_classes.Mythic,
    instance_name: str,
    c2_profile_name: str,
) -> GetC2InstanceResponse:
    """Get a saved C2 profile instance by name.

    Each saved instance is stored as one row per parameter in Mythic's DB.
    This function assembles them into a single parameter dict.
    """
    c2_profile_id = await _resolve_c2_profile_id(mythic_instance, c2_profile_name)

    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=GET_C2_INSTANCE_QUERY,
        variables={"instance_name": instance_name, "c2_profile_id": c2_profile_id},
    )

    rows = resp.get("c2profileparametersinstance", [])
    if not rows:
        raise C2InstanceNotFoundError(instance_name)

    # Assemble per-parameter rows into a single dict
    c2_params = {}
    for row in rows:
        param_info = row.get("c2profileparameter", {})
        param_name = param_info.get("name", "")
        parameter_type = param_info.get("parameter_type", "String")
        if param_name:
            c2_params[param_name] = _coerce_c2_parameter_value(
                parameter_type,
                row.get("value", ""),
            )

    return GetC2InstanceResponse(
        instance_name=instance_name,
        c2_profile_name=c2_profile_name,
        c2_parameters=c2_params,
    )


async def resolve_c2_instance_by_name(
    mythic_instance: mythic_classes.Mythic,
    instance_name: str,
) -> GetC2InstanceResponse:
    """Resolve a saved C2 instance by name within the current operation."""
    matches = [
        instance
        for instance in (await list_c2_instances(mythic_instance)).instances
        if instance.instance_name == instance_name
    ]
    if not matches:
        raise C2InstanceNotFoundError(instance_name)
    if len(matches) > 1:
        raise C2InstanceAmbiguousError(
            instance_name,
            [match.c2_profile_name for match in matches],
        )
    return await get_c2_instance(
        mythic_instance,
        instance_name=instance_name,
        c2_profile_name=matches[0].c2_profile_name,
    )


async def delete_c2_instance(
    mythic_instance: mythic_classes.Mythic,
    instance_name: str,
    c2_profile_name: str,
) -> DeleteC2InstanceResponse:
    """Delete a saved C2 profile instance from the Mythic server."""
    c2_profile_id = await _resolve_c2_profile_id(mythic_instance, c2_profile_name)

    resp = await mythic_utilities.graphql_post(
        mythic=mythic_instance,
        query=DELETE_C2_INSTANCE_MUTATION,
        variables={"instance_name": instance_name, "c2_profile_id": c2_profile_id},
    )

    affected = resp.get("delete_c2profileparametersinstance", {}).get("affected_rows", 0)
    if affected == 0:
        raise C2InstanceNotFoundError(instance_name)

    return DeleteC2InstanceResponse(
        instance_name=instance_name,
    )


# --- Exception Classes ---


class C2ProfileNotFoundError(Exception):
    """Raised when a C2 profile is not found on the Mythic server."""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        super().__init__(f"C2 profile '{profile_name}' not found or has no parameters")


class C2InstanceNotFoundError(Exception):
    """Raised when a saved C2 instance is not found."""

    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        super().__init__(f"Saved instance '{instance_name}' not found")


class C2InstanceAmbiguousError(Exception):
    """Raised when a saved C2 instance name matches multiple C2 profiles."""

    def __init__(self, instance_name: str, c2_profile_names: list[str]):
        self.instance_name = instance_name
        self.c2_profile_names = c2_profile_names
        profiles = ", ".join(sorted(c2_profile_names))
        super().__init__(
            f"Saved instance '{instance_name}' is ambiguous across C2 profiles: {profiles}"
        )


class C2InstanceCreateError(Exception):
    """Raised when creating a C2 instance fails."""


# --- Tool Entry Points ---


async def core_list_c2_profiles(
    ctx: Context,
) -> ListC2ProfilesResponse | C2ProfileErrorResponse:
    """MCP tool entry point for listing C2 profiles."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_c2_profiles(mythic_ctx.mythic)
    except Exception as e:
        logger.exception("Unexpected error in core_list_c2_profiles")
        return C2ProfileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )


async def core_get_c2_profile_parameters(
    ctx: Context,
    c2_profile_name: str,
) -> GetC2ProfileParametersResponse | C2ProfileErrorResponse:
    """MCP tool entry point for getting C2 profile parameters."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_c2_profile_parameters(mythic_ctx.mythic, c2_profile_name)
    except C2ProfileNotFoundError as e:
        return C2ProfileErrorResponse(error=str(e), error_type="not_found")
    except Exception as e:
        logger.exception("Unexpected error in core_get_c2_profile_parameters")
        return C2ProfileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )


async def core_create_c2_instance(
    ctx: Context,
    instance_name: str,
    c2_profile_name: str,
    c2_parameters: str,
) -> CreateC2InstanceResponse | C2ProfileErrorResponse:
    """MCP tool entry point for creating a saved C2 instance."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        params = json.loads(c2_parameters)
    except json.JSONDecodeError as e:
        return C2ProfileErrorResponse(
            error=f"Invalid JSON for c2_parameters: {e}",
            error_type="invalid_input",
        )

    if not isinstance(params, dict):
        return C2ProfileErrorResponse(
            error="c2_parameters must be a JSON object",
            error_type="invalid_input",
        )

    try:
        return await create_c2_instance(
            mythic_ctx.mythic, instance_name, c2_profile_name, params,
        )
    except C2InstanceCreateError as e:
        return C2ProfileErrorResponse(error=str(e), error_type="not_found")
    except Exception as e:
        error_msg = str(e)
        if "Failed to find" in error_msg:
            return C2ProfileErrorResponse(error=error_msg, error_type="not_found")
        logger.exception("Unexpected error in core_create_c2_instance")
        return C2ProfileErrorResponse(
            error=error_msg,
            error_type="connection_error",
        )


async def core_list_c2_instances(
    ctx: Context,
) -> ListC2InstancesResponse | C2ProfileErrorResponse:
    """MCP tool entry point for listing saved C2 instances."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await list_c2_instances(mythic_ctx.mythic)
    except Exception as e:
        logger.exception("Unexpected error in core_list_c2_instances")
        return C2ProfileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )


async def core_get_c2_instance(
    ctx: Context,
    instance_name: str,
    c2_profile_name: str,
) -> GetC2InstanceResponse | C2ProfileErrorResponse:
    """MCP tool entry point for getting a saved C2 instance."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await get_c2_instance(mythic_ctx.mythic, instance_name, c2_profile_name)
    except (C2InstanceNotFoundError, C2ProfileNotFoundError) as e:
        return C2ProfileErrorResponse(error=str(e), error_type="not_found")
    except Exception as e:
        logger.exception("Unexpected error in core_get_c2_instance")
        return C2ProfileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )


async def core_delete_c2_instance(
    ctx: Context,
    instance_name: str,
    c2_profile_name: str,
) -> DeleteC2InstanceResponse | C2ProfileErrorResponse:
    """MCP tool entry point for deleting a saved C2 instance."""
    mythic_ctx: MythicContext = ctx.request_context.lifespan_context

    try:
        return await delete_c2_instance(mythic_ctx.mythic, instance_name, c2_profile_name)
    except (C2InstanceNotFoundError, C2ProfileNotFoundError) as e:
        return C2ProfileErrorResponse(error=str(e), error_type="not_found")
    except Exception as e:
        logger.exception("Unexpected error in core_delete_c2_instance")
        return C2ProfileErrorResponse(
            error=str(e),
            error_type="connection_error",
        )
