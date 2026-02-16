"""YAML-based agent plugin configuration loader.

Loads agent plugin definitions from YAML configuration files, validates them
using Pydantic models, and generates AgentPlugin instances with dynamic
parameter models and handler functions.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from mythicmcp.plugins.base import AgentPlugin, ToolDefinition

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context

logger = logging.getLogger(__name__)

# Reserved parameter names that cannot be used in YAML config
RESERVED_PARAM_NAMES = frozenset({"callback_id", "timeout", "ctx", "context", "self"})

# Valid operating systems
VALID_OS = frozenset({"Windows", "Linux", "macOS"})

# Valid parameter types
VALID_PARAM_TYPES = frozenset({"string", "integer", "boolean"})

# Type mapping from YAML type strings to Python types
TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "boolean": bool,
}

# Agent name pattern: lowercase alphanumeric + hyphens, 1-50 chars
AGENT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")

# Command name pattern: lowercase alphanumeric + underscores, 1-50 chars
COMMAND_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]{0,49}$")


# --- Pydantic Config Models (T002) ---


class ParameterConfigModel(BaseModel):
    """Validates a single parameter definition from YAML config."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    role: str = "task"
    min: int | None = None
    max: int | None = None
    choices: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError(f"Parameter name '{v}' is not a valid Python identifier")
        if v in RESERVED_PARAM_NAMES:
            raise ValueError(
                f"Parameter name '{v}' is reserved (cannot use: {', '.join(sorted(RESERVED_PARAM_NAMES))})"
            )
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_PARAM_TYPES:
            raise ValueError(
                f"Unsupported parameter type '{v}' (must be one of: {', '.join(sorted(VALID_PARAM_TYPES))})"
            )
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("task", "meta"):
            raise ValueError(f"Invalid role '{v}' (must be 'task' or 'meta')")
        return v

    @model_validator(mode="after")
    def validate_constraints(self) -> ParameterConfigModel:
        # min/max only valid for integer type
        if self.type != "integer":
            if self.min is not None:
                raise ValueError(
                    f"Parameter '{self.name}': 'min' is only valid for integer type"
                )
            if self.max is not None:
                raise ValueError(
                    f"Parameter '{self.name}': 'max' is only valid for integer type"
                )

        # choices only valid for string type
        if self.type != "string" and self.choices is not None:
            raise ValueError(
                f"Parameter '{self.name}': 'choices' is only valid for string type"
            )

        # min must be <= max
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(
                f"Parameter '{self.name}': min ({self.min}) must be <= max ({self.max})"
            )

        # default must match declared type
        if self.default is not None:
            expected_type = TYPE_MAP[self.type]
            if not isinstance(self.default, expected_type):
                # Allow int for bool since YAML may parse True/False differently
                if not (self.type == "boolean" and isinstance(self.default, bool)):
                    raise ValueError(
                        f"Parameter '{self.name}': default value {self.default!r} "
                        f"does not match type '{self.type}'"
                    )

        # If default is provided, required is implicitly false
        if self.default is not None:
            self.required = False

        return self


class CommandConfigModel(BaseModel):
    """Validates a single command definition from YAML config."""

    name: str
    description: str
    mythic_command: str | None = None
    timeout: int = 60
    parameters: list[ParameterConfigModel] = []

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not COMMAND_NAME_PATTERN.match(v):
            raise ValueError(
                f"Command name '{v}' must be lowercase alphanumeric with optional "
                f"underscores, 1-50 characters"
            )
        if v in ("ctx", "context", "self"):
            raise ValueError(f"Command name '{v}' is a reserved word")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Command description must not be empty")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v < 30 or v > 300:
            raise ValueError(f"Timeout {v} must be between 30 and 300 seconds")
        return v

    @model_validator(mode="after")
    def set_mythic_command_default(self) -> CommandConfigModel:
        if self.mythic_command is None:
            self.mythic_command = self.name
        return self

    @model_validator(mode="after")
    def validate_unique_param_names(self) -> CommandConfigModel:
        names = [p.name for p in self.parameters]
        seen: set[str] = set()
        for name in names:
            if name in seen:
                raise ValueError(
                    f"Duplicate parameter name '{name}' in command '{self.name}'"
                )
            seen.add(name)
        return self


class AgentConfigModel(BaseModel):
    """Validates a complete agent configuration from YAML config."""

    name: str
    description: str
    supported_os: list[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not AGENT_NAME_PATTERN.match(v):
            raise ValueError(
                f"Agent name '{v}' must be lowercase alphanumeric with optional "
                f"hyphens, 1-50 characters, starting with alphanumeric"
            )
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Agent description must not be empty")
        return v

    @field_validator("supported_os")
    @classmethod
    def validate_supported_os(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one supported OS must be specified")
        for os_name in v:
            if os_name not in VALID_OS:
                raise ValueError(
                    f"Unsupported OS '{os_name}' (must be one of: {', '.join(sorted(VALID_OS))})"
                )
        return v


class YamlConfigModel(BaseModel):
    """Top-level YAML configuration model."""

    agent: AgentConfigModel
    commands: list[CommandConfigModel]
    metadata: dict[str, Any] | None = None

    model_config = {"extra": "allow"}

    @field_validator("commands")
    @classmethod
    def validate_commands_not_empty(cls, v: list[CommandConfigModel]) -> list[CommandConfigModel]:
        if not v:
            raise ValueError("At least one command must be defined")
        return v

    @model_validator(mode="after")
    def validate_unique_command_names(self) -> YamlConfigModel:
        names = [c.name for c in self.commands]
        seen: set[str] = set()
        for name in names:
            if name in seen:
                raise ValueError(f"Duplicate command name '{name}' in agent config")
            seen.add(name)
        return self

    @model_validator(mode="after")
    def warn_extra_fields(self) -> YamlConfigModel:
        if self.model_extra:
            extra_keys = ", ".join(sorted(self.model_extra.keys()))
            logger.warning(f"Unrecognized top-level keys in config: {extra_keys}")
        return self


# --- YAML Parsing (T003) ---


class YamlConfigError:
    """Structured error from YAML config validation."""

    def __init__(self, file_path: str, agent_name: str, errors: list[dict[str, str]]):
        self.file_path = file_path
        self.agent_name = agent_name
        self.errors = errors

    def __str__(self) -> str:
        error_lines = [f"  - {e['field']}: {e['message']}" for e in self.errors]
        return (
            f"Config validation failed for '{self.file_path}' "
            f"(agent: {self.agent_name}):\n" + "\n".join(error_lines)
        )


def parse_yaml_config(file_path: Path) -> YamlConfigModel | YamlConfigError:
    """Parse and validate a YAML configuration file.

    Args:
        file_path: Path to the YAML configuration file.

    Returns:
        Validated YamlConfigModel on success, or YamlConfigError on failure.
    """
    try:
        with open(file_path) as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return YamlConfigError(
            file_path=str(file_path),
            agent_name="unknown",
            errors=[{"field": "yaml", "message": f"YAML parse error: {e}"}],
        )

    if raw_data is None:
        return YamlConfigError(
            file_path=str(file_path),
            agent_name="unknown",
            errors=[{"field": "yaml", "message": "File is empty or contains only comments"}],
        )

    if not isinstance(raw_data, dict):
        return YamlConfigError(
            file_path=str(file_path),
            agent_name="unknown",
            errors=[{"field": "yaml", "message": "Top-level structure must be a mapping"}],
        )

    # Try to extract agent name for error reporting
    agent_name = "unknown"
    if isinstance(raw_data.get("agent"), dict):
        agent_name = raw_data["agent"].get("name", "unknown")

    try:
        config = YamlConfigModel.model_validate(raw_data)
        return config
    except Exception as e:
        errors = _extract_validation_errors(e)
        return YamlConfigError(
            file_path=str(file_path),
            agent_name=agent_name,
            errors=errors,
        )


def _extract_validation_errors(exc: Exception) -> list[dict[str, str]]:
    """Extract structured error info from a Pydantic validation exception."""
    from pydantic import ValidationError

    if isinstance(exc, ValidationError):
        errors = []
        for err in exc.errors():
            loc_parts = [str(p) for p in err.get("loc", [])]
            field_path = ".".join(loc_parts) if loc_parts else "unknown"
            errors.append({
                "field": field_path,
                "message": err.get("msg", str(err)),
            })
        return errors

    return [{"field": "unknown", "message": str(exc)}]


# --- Dynamic Pydantic Model Builder (T004) ---


def build_parameter_model(
    command_config: CommandConfigModel, agent_name: str
) -> type[BaseModel]:
    """Build a dynamic Pydantic model class for a command's parameters.

    Creates a model with:
    - callback_id (int, required) as first field
    - All declared parameters mapped to Python types with constraints
    - timeout (int, optional with command default) as last field

    Args:
        command_config: The command configuration to build a model for.
        agent_name: The agent name (used for model class naming).

    Returns:
        A Pydantic BaseModel subclass for the command's parameters.
    """
    field_definitions: dict[str, Any] = {}

    # First field: callback_id (required)
    field_definitions["callback_id"] = (
        int,
        Field(..., description="Callback ID to execute on"),
    )

    # Declared parameters in order
    for param in command_config.parameters:
        python_type = TYPE_MAP[param.type]
        field_kwargs: dict[str, Any] = {"description": param.description}

        if param.default is not None:
            field_kwargs["default"] = param.default
        elif not param.required:
            field_kwargs["default"] = None

        # Integer constraints
        if param.type == "integer":
            if param.min is not None:
                field_kwargs["ge"] = param.min
            if param.max is not None:
                field_kwargs["le"] = param.max

        if param.required and param.default is None:
            field_definitions[param.name] = (python_type, Field(..., **field_kwargs))
        else:
            field_definitions[param.name] = (python_type, Field(**field_kwargs))

    # Last field: timeout (optional with command default)
    field_definitions["timeout"] = (
        int,
        Field(
            default=command_config.timeout,
            ge=30,
            le=300,
            description="Timeout in seconds",
        ),
    )

    # Create model class name
    model_name = f"{agent_name.title().replace('-', '')}_{command_config.name.title().replace('_', '')}Params"

    # Create the dynamic model
    model = type(model_name, (BaseModel,), {
        "__annotations__": {k: v[0] for k, v in field_definitions.items()},
        **{k: v[1] for k, v in field_definitions.items()},
    })

    return model


# --- Handler Generator (T005) ---


def build_handler(
    agent_config: AgentConfigModel,
    command_config: CommandConfigModel,
) -> Callable[[Any, Any], Coroutine[Any, Any, Any]]:
    """Generate an async handler function for a command.

    The handler extracts callback_id and timeout from params, collects all
    task-role parameters into a dict, and calls execute_with_validation.

    Args:
        agent_config: The agent configuration.
        command_config: The command configuration.

    Returns:
        An async handler function compatible with ToolDefinition.
    """
    agent_name = agent_config.name
    mythic_command = command_config.mythic_command or command_config.name

    # Pre-compute which parameters are task-role
    task_param_names = [
        p.name for p in command_config.parameters if p.role == "task"
    ]

    async def handler(ctx: Context, params: Any) -> Any:
        from mythicmcp.plugins.executor import execute_with_validation

        callback_id = params.callback_id
        timeout = params.timeout

        # Collect task-role parameters
        task_params = {}
        for param_name in task_param_names:
            value = getattr(params, param_name)
            task_params[param_name] = value

        return await execute_with_validation(
            ctx=ctx,
            callback_id=callback_id,
            expected_agent_type=agent_name,
            command_name=mythic_command,
            parameters=task_params,
            timeout=timeout,
        )

    return handler


# --- YAML-to-AgentPlugin Adapter (T006) ---


class YamlAgentPlugin(AgentPlugin):
    """AgentPlugin implementation backed by YAML configuration.

    Wraps a validated YamlConfigModel and generates ToolDefinition
    instances from the command configurations.
    """

    def __init__(self, config: YamlConfigModel):
        super().__init__()
        self.agent_name = config.agent.name
        self.agent_description = config.agent.description
        self.supported_os = list(config.agent.supported_os)
        self._config = config
        self._tools: list[ToolDefinition] | None = None

    def get_tools(self) -> list[ToolDefinition]:
        if self._tools is not None:
            return self._tools

        self._tools = []
        for cmd in self._config.commands:
            param_model = build_parameter_model(cmd, self.agent_name)
            handler = build_handler(self._config.agent, cmd)
            self._tools.append(
                ToolDefinition(
                    name=cmd.name,
                    description=cmd.description,
                    parameters=param_model,
                    handler=handler,
                )
            )

        return self._tools


def load_yaml_plugin(file_path: Path) -> AgentPlugin | YamlConfigError:
    """Load a YAML configuration file and produce an AgentPlugin.

    Args:
        file_path: Path to the YAML configuration file.

    Returns:
        AgentPlugin instance on success, or YamlConfigError on failure.
    """
    result = parse_yaml_config(file_path)
    if isinstance(result, YamlConfigError):
        return result

    return YamlAgentPlugin(result)


# --- Config Discovery (T008) ---


def discover_yaml_configs(directory: Path) -> list[Path]:
    """Discover YAML configuration files in a directory.

    Finds .yaml and .yml files, skipping files starting with _ or .

    Args:
        directory: Directory to search for YAML files.

    Returns:
        Sorted list of paths to YAML configuration files.
    """
    if not directory.exists():
        logger.info(f"Config directory does not exist: {directory}")
        return []

    yaml_files = []
    for pattern in ("*.yaml", "*.yml"):
        for path in directory.glob(pattern):
            if path.name.startswith("_") or path.name.startswith("."):
                continue
            yaml_files.append(path)

    # Sort for deterministic load order
    yaml_files.sort()

    logger.debug(f"Discovered {len(yaml_files)} YAML config files in {directory}")
    return yaml_files
