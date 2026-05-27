"""Unit tests for mythicmcp.tools.commands."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.lab_config import UNC_MISSING_SHARE, UNC_OTHER_SHARE, UNC_SHARE
from mythicmcp.tools.commands import (
    AmbiguousCommandError,
    CallbackNotFoundError,
    LoadedCommandNotFoundError,
    _fetch_callback_commands,
    _example_value_for_parameter,
    execute_callback_command,
    get_callback_command,
    list_callback_commands,
)


def _callback_query_result(*, active: bool = True, duplicate_shell: bool = False) -> dict:
    """Build a callback loadedcommands query result."""
    loadedcommands = [
        {
            "command": {
                "cmd": "whoami",
                "help_cmd": "whoami",
                "description": "Get current username",
                "attributes": {"builtin": False},
                "payloadtype": {"name": "apollo"},
            }
        },
        {
            "command": {
                "cmd": "shell",
                "help_cmd": "shell [command]",
                "description": "Run a shell command",
                "attributes": {"builtin": False},
                "payloadtype": {"name": "apollo"},
            }
        },
        {
            "command": {
                "cmd": "nb_md5",
                "help_cmd": "nb_md5 <path>",
                "description": "Compute the MD5 hash of a file.",
                "attributes": {"builtin": False, "suggested_command": True},
                "payloadtype": {"name": "nano_bofs"},
                "commandparameters": [
                    {
                        "name": "path",
                        "cli_name": "path",
                        "display_name": "Path",
                        "description": "File path to hash",
                        "placeholder": r"C:\Windows\win.ini",
                        "example": r"C:\Windows\win.ini",
                        "type": "String",
                        "default_value": "",
                        "required": True,
                        "parameter_group_name": "Default",
                        "ui_position": 1,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                ],
            }
        },
        {
            "command": {
                "cmd": "nb_wmi_query",
                "help_cmd": "nb_wmi_query <query> [server] [namespace]",
                "description": "Run a general WMI query.",
                "attributes": {"builtin": False, "suggested_command": True},
                "payloadtype": {"name": "nano_bofs"},
                "commandparameters": [
                    {
                        "name": "query",
                        "cli_name": "query",
                        "display_name": "Query",
                        "description": "WQL query to run",
                        "placeholder": "SELECT * FROM Win32_OperatingSystem",
                        "example": "SELECT * FROM Win32_OperatingSystem",
                        "type": "String",
                        "default_value": "",
                        "required": True,
                        "parameter_group_name": "Default",
                        "ui_position": 1,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                    {
                        "name": "server",
                        "cli_name": "server",
                        "display_name": "Server",
                        "description": "Optional server",
                        "placeholder": "",
                        "example": "",
                        "type": "String",
                        "default_value": "",
                        "required": False,
                        "parameter_group_name": "Default",
                        "ui_position": 2,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                    {
                        "name": "namespace",
                        "cli_name": "namespace",
                        "display_name": "Namespace",
                        "description": "Optional namespace",
                        "placeholder": r"root\cimv2",
                        "example": r"root\cimv2",
                        "type": "String",
                        "default_value": "",
                        "required": False,
                        "parameter_group_name": "Default",
                        "ui_position": 3,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                ],
            }
        },
        {
            "command": {
                "cmd": "nb_netuse_add",
                "help_cmd": "nb_netuse_add <share> [username] [password] [device] [persist] [require_privacy]",
                "description": "Create a new network-use connection.",
                "attributes": {"builtin": False, "suggested_command": True},
                "payloadtype": {"name": "nano_bofs"},
                "commandparameters": [
                    {
                        "name": "share",
                        "cli_name": "share",
                        "display_name": "Share",
                        "description": "UNC share like \\\\HOST\\Share",
                        "placeholder": UNC_SHARE,
                        "example": UNC_SHARE,
                        "type": "String",
                        "default_value": "",
                        "required": True,
                        "parameter_group_name": "Default",
                        "ui_position": 1,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                    {
                        "name": "persist",
                        "cli_name": "persist",
                        "display_name": "Persist",
                        "description": "Persist connection",
                        "placeholder": "",
                        "example": "",
                        "type": "Boolean",
                        "default_value": "",
                        "required": False,
                        "parameter_group_name": "Default",
                        "ui_position": 2,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                ],
            }
        },
        {
            "command": {
                "cmd": "nb_netuse_delete",
                "help_cmd": "nb_netuse_delete <target>",
                "description": "Delete a network-use connection.",
                "attributes": {"builtin": False, "suggested_command": True},
                "payloadtype": {"name": "nano_bofs"},
                "commandparameters": [
                    {
                        "name": "target",
                        "cli_name": "target",
                        "display_name": "Target",
                        "description": "UNC share target",
                        "placeholder": "",
                        "example": UNC_MISSING_SHARE,
                        "type": "String",
                        "default_value": "",
                        "required": True,
                        "parameter_group_name": "Default",
                        "ui_position": 1,
                        "choices": [],
                        "choices_are_all_commands": False,
                        "choices_are_loaded_commands": False,
                        "choice_filter_by_command_attributes": {},
                        "supported_agents": [],
                        "supported_agent_build_parameters": {},
                        "dynamic_query_function": "",
                    },
                ],
            }
        },
    ]
    if duplicate_shell:
        loadedcommands.append(
            {
                "command": {
                    "cmd": "shell",
                    "help_cmd": "shell",
                    "description": "Augmented shell",
                    "attributes": {"builtin": False},
                    "payloadtype": {"name": "nano_bofs"},
                }
            }
        )

    return {
        "callback_by_pk": {
            "id": 39,
            "display_id": 36,
            "active": active,
            "payload": {"payloadtype": {"name": "apollo"}},
            "loadedcommands": loadedcommands,
        }
    }


class TestListCallbackCommands:
    """Tests for list_callback_commands."""

    @pytest.mark.asyncio
    async def test_returns_native_and_augmented_commands(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await list_callback_commands(mock_mythic, 39)

            assert result.callback_id == 39
            assert result.display_id == 36
            assert result.agent_type == "apollo"
            assert result.count == 6
            assert [c.command_name for c in result.commands] == [
                "nb_md5",
                "nb_netuse_add",
                "nb_netuse_delete",
                "nb_wmi_query",
                "shell",
                "whoami",
            ]
            assert result.commands[0].source == "nano_bofs"
            assert result.commands[0].is_native is False
            assert result.commands[4].source == "apollo"
            assert result.commands[4].is_native is True

    @pytest.mark.asyncio
    async def test_source_filter_narrows_results(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await list_callback_commands(mock_mythic, 39, source="nano_bofs")

            assert result.count == 4
            assert result.source == "nano_bofs"
            assert [command.command_name for command in result.commands] == [
                "nb_md5",
                "nb_netuse_add",
                "nb_netuse_delete",
                "nb_wmi_query",
            ]


class TestGetCallbackCommand:
    """Tests for get_callback_command."""

    @pytest.mark.asyncio
    async def test_returns_ordered_parameter_metadata(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await get_callback_command(mock_mythic, 39, "nb_wmi_query")

            assert result.command.command_name == "nb_wmi_query"
            assert result.command.source == "nano_bofs"
            assert result.command.argument_mode == "json_object"
            assert result.command.execution_usage == '{"query":"SELECT * FROM Win32_OperatingSystem"}'
            assert result.command.example_arguments == '{"query":"SELECT * FROM Win32_OperatingSystem"}'
            assert result.command.zero_arg_example is None
            assert "JSON object string" in result.command.execution_notes
            assert "execution_usage" in result.command.execution_notes
            assert [p.cli_name for p in result.command.parameters] == [
                "query",
                "server",
                "namespace",
            ]

    @pytest.mark.asyncio
    async def test_returns_json_hints_for_single_parameter_command(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await get_callback_command(mock_mythic, 39, "nb_md5")

            assert result.command.argument_mode == "json_object"
            assert result.command.execution_usage == '{"path":"C:\\\\Windows\\\\win.ini"}'
            assert result.command.example_arguments == '{"path":"C:\\\\Windows\\\\win.ini"}'
            assert result.command.zero_arg_example is None

    @pytest.mark.asyncio
    async def test_placeholder_beats_generic_heuristics_for_share_values(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await get_callback_command(mock_mythic, 39, "nb_netuse_add")

            assert result.command.execution_usage == (
                '{"share":"' + UNC_SHARE.replace("\\", "\\\\") + '"}'
            )
            assert result.command.example_arguments == (
                '{"share":"' + UNC_SHARE.replace("\\", "\\\\") + '"}'
            )
            assert "persist" not in result.command.execution_usage

    @pytest.mark.asyncio
    async def test_example_beats_generic_heuristics_for_target_values(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await get_callback_command(mock_mythic, 39, "nb_netuse_delete")

            assert result.command.execution_usage == (
                '{"target":"' + UNC_MISSING_SHARE.replace("\\", "\\\\") + '"}'
            )
            assert result.command.example_arguments == (
                '{"target":"' + UNC_MISSING_SHARE.replace("\\", "\\\\") + '"}'
            )

    @pytest.mark.asyncio
    async def test_returns_cli_hints_for_raw_text_and_zero_arg_commands(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            shell_result = await get_callback_command(mock_mythic, 39, "shell")
            whoami_result = await get_callback_command(mock_mythic, 39, "whoami")

            assert shell_result.command.argument_mode == "cli"
            assert shell_result.command.execution_usage == "<raw command-line text>"
            assert shell_result.command.example_arguments == "<raw command-line text>"
            assert shell_result.command.zero_arg_example is None
            assert "raw command-line text" in shell_result.command.execution_notes
            assert whoami_result.command.argument_mode == "cli"
            assert whoami_result.command.execution_usage == ""
            assert whoami_result.command.example_arguments == ""
            assert whoami_result.command.zero_arg_example == ""

    @pytest.mark.asyncio
    async def test_retries_without_optional_metadata_when_graphql_schema_is_older(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = [
                Exception(
                    "validation-failed: field 'placeholder' not found in type: "
                    "'commandparameters'"
                ),
                _callback_query_result(),
            ]

            result = await _fetch_callback_commands(
                mock_mythic, callback_id=39, include_parameters=True
            )

            assert result["id"] == 39
            assert mock_query.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_for_ambiguous_name_without_source(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result(duplicate_shell=True)

            with pytest.raises(AmbiguousCommandError, match="multiple sources"):
                await get_callback_command(mock_mythic, 39, "shell")

    @pytest.mark.asyncio
    async def test_raises_for_missing_callback(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"callback_by_pk": None}

            with pytest.raises(CallbackNotFoundError):
                await get_callback_command(mock_mythic, 39, "shell")


class TestExampleArgumentHeuristics:
    """Tests for metadata-derived example argument values."""

    def test_probe_style_host_validation_does_not_turn_into_path_example(self):
        host_value = _example_value_for_parameter(
            {
                "name": "host",
                "display_name": "Host",
                "description": "Target host name or IPv4 address. Must not be a URL or path.",
                "type": "String",
                "default_value": "",
                "choices": [],
            }
        )
        port_value = _example_value_for_parameter(
            {
                "name": "port",
                "display_name": "Port",
                "description": "Target TCP port.",
                "type": "Number",
                "default_value": 0,
                "choices": [],
            }
        )

        assert host_value == "10.0.0.5"
        assert port_value == 0

    def test_placeholder_beats_example_default_and_heuristics(self):
        value = _example_value_for_parameter(
            {
                "name": "share",
                "display_name": "Share",
                "description": "UNC share like \\\\HOST\\Share",
                "placeholder": UNC_SHARE,
                "example": UNC_OTHER_SHARE,
                "type": "String",
                "default_value": r"\\default\share",
                "choices": [r"\\choice\share"],
            }
        )

        assert value == UNC_SHARE

    def test_example_beats_default_and_heuristics(self):
        value = _example_value_for_parameter(
            {
                "name": "target",
                "display_name": "Target",
                "description": "UNC share target",
                "placeholder": "",
                "example": UNC_MISSING_SHARE,
                "type": "String",
                "default_value": "fallback",
                "choices": ["choice"],
            }
        )

        assert value == UNC_MISSING_SHARE

    def test_description_example_beats_generic_heuristics(self):
        value = _example_value_for_parameter(
            {
                "name": "share",
                "display_name": "Share",
                "description": (
                    r"UNC share like \\HOST\Share. Shape: UNC share path. "
                    f"Example: {UNC_SHARE} Validation: Must be a UNC path."
                ),
                "placeholder": "",
                "example": "",
                "type": "String",
                "default_value": "",
                "choices": [],
            }
        )

        assert value == UNC_SHARE

    def test_default_beats_choices_and_heuristics(self):
        value = _example_value_for_parameter(
            {
                "name": "server",
                "display_name": "Server",
                "description": "Remote host name",
                "placeholder": "",
                "example": "",
                "type": "String",
                "default_value": "dc01",
                "choices": ["10.0.0.5"],
            }
        )

        assert value == "dc01"


class TestExecuteCallbackCommand:
    """Tests for execute_callback_command."""

    @pytest.mark.asyncio
    async def test_rejects_command_not_loaded(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result()

            result = await execute_callback_command(mock_mythic, 39, "does_not_exist")

            assert result.success is False
            assert result.error_type == "command_not_loaded"

    @pytest.mark.asyncio
    async def test_uses_canonical_callback_id_to_resolve_display_id(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query, patch(
            "mythic.mythic.issue_task", new_callable=AsyncMock
        ) as mock_issue, patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_output:
            mock_query.return_value = _callback_query_result()
            mock_issue.return_value = {
                "id": 1200,
                "display_id": 88,
                "status": "completed",
                "error": "",
            }
            mock_output.return_value = [
                {"id": 1, "response_text": "b2s=", "timestamp": "2026-05-06T12:00:00Z"}
            ]

            result = await execute_callback_command(
                mock_mythic, 39, "nb_wmi_query", arguments="SELECT * FROM Win32_OperatingSystem"
            )

            assert result.success is True
            assert result.callback_id == 39
            assert result.display_id == 36
            assert result.source == "nano_bofs"
            assert result.task_id == 1200
            assert result.task_display_id == 88
            assert result.output == "ok"
            assert mock_issue.await_args.kwargs["callback_display_id"] == 36
            assert mock_issue.await_args.kwargs["payload_type"] == "nano_bofs"
            assert mock_issue.await_args.kwargs["parameters"] == "SELECT * FROM Win32_OperatingSystem"

    @pytest.mark.asyncio
    async def test_ambiguous_name_requires_source(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result(duplicate_shell=True)

            result = await execute_callback_command(mock_mythic, 39, "shell")

            assert result.success is False
            assert result.error_type == "ambiguous_command"

    @pytest.mark.asyncio
    async def test_source_disambiguates_duplicate_command(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query, patch(
            "mythic.mythic.issue_task", new_callable=AsyncMock
        ) as mock_issue, patch(
            "mythic.mythic.get_all_task_output_by_id", new_callable=AsyncMock
        ) as mock_output:
            mock_query.return_value = _callback_query_result(duplicate_shell=True)
            mock_issue.return_value = {
                "id": 1201,
                "display_id": 89,
                "status": "completed",
                "error": "",
            }
            mock_output.return_value = []

            result = await execute_callback_command(
                mock_mythic, 39, "shell", arguments="whoami", source="apollo"
            )

            assert result.success is True
            assert result.source == "apollo"
            assert mock_issue.await_args.kwargs["payload_type"] == "apollo"

    @pytest.mark.asyncio
    async def test_inactive_callback_is_rejected(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = _callback_query_result(active=False)

            result = await execute_callback_command(mock_mythic, 39, "shell")

            assert result.success is False
            assert result.error_type == "callback_inactive"

    @pytest.mark.asyncio
    async def test_timeout_recovers_created_task_ids(self):
        mock_mythic = MagicMock()
        mock_mythic.current_operation_id = 3

        with patch("mythic.mythic.execute_custom_query", new_callable=AsyncMock) as mock_query, patch(
            "mythic.mythic.issue_task", new_callable=AsyncMock
        ) as mock_issue, patch(
            "mythic.mythic.get_all_tasks", new_callable=AsyncMock
        ) as mock_tasks:
            mock_query.return_value = _callback_query_result()
            mock_issue.side_effect = asyncio.TimeoutError()
            mock_tasks.return_value = [
                {
                    "id": 1086,
                    "display_id": 1006,
                    "command_name": "nb_md5",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "original_params": '{"path":"C:\\\\Windows\\\\win.ini"}',
                    "display_params": '{"path":"C:\\\\Windows\\\\win.ini"}',
                }
            ]

            result = await execute_callback_command(
                mock_mythic,
                39,
                "nb_md5",
                arguments='{"path":"C:\\\\Windows\\\\win.ini"}',
                source="nano_bofs",
                timeout=20,
            )

            assert result.success is False
            assert result.error_type == "timeout"
            assert result.task_id == 1086
            assert result.task_display_id == 1006
            assert "Inspect core_get_task_output next" in result.error
