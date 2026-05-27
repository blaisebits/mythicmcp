from __future__ import annotations

from types import SimpleNamespace

import pytest

from mythicmcp.models import CallbackAgentInfo, ExecuteTaskResponse, TaskStatus
from mythicmcp.plugins.executor import (
    CallbackNotFoundError,
    execute_task,
    execute_with_validation,
    get_callback_agent_type,
)


def _build_ctx() -> SimpleNamespace:
    return SimpleNamespace(
        request_context=SimpleNamespace(
            lifespan_context=SimpleNamespace(mythic=object())
        )
    )


@pytest.mark.asyncio
async def test_get_callback_agent_type_accepts_internal_id(monkeypatch: pytest.MonkeyPatch):
    async def fake_execute_custom_query(*args, **kwargs):
        assert kwargs["variables"] == {"callback_id": 5}
        return {
            "callback": [
                {
                    "id": 5,
                    "display_id": 2,
                    "active": True,
                    "payload": {"payloadtype": {"name": "apollo"}},
                }
            ]
        }

    monkeypatch.setattr("mythic.mythic.execute_custom_query", fake_execute_custom_query)

    result = await get_callback_agent_type(_build_ctx(), 5)

    assert result.callback_id == 5
    assert result.display_id == 2
    assert result.agent_type == "apollo"
    assert result.active is True


@pytest.mark.asyncio
async def test_get_callback_agent_type_rejects_display_id_only_lookup(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_execute_custom_query(*args, **kwargs):
        assert kwargs["variables"] == {"callback_id": 2}
        return {"callback": []}

    monkeypatch.setattr("mythic.mythic.execute_custom_query", fake_execute_custom_query)

    with pytest.raises(CallbackNotFoundError, match="Callback with ID 2 not found"):
        await get_callback_agent_type(_build_ctx(), 2)


@pytest.mark.asyncio
async def test_get_callback_agent_type_prefers_true_callback_id_over_same_display_id(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_execute_custom_query(*args, **kwargs):
        assert kwargs["variables"] == {"callback_id": 5}
        return {
            "callback": [
                {
                    "id": 5,
                    "display_id": 2,
                    "active": True,
                    "payload": {"payloadtype": {"name": "apollo"}},
                }
            ]
        }

    monkeypatch.setattr("mythic.mythic.execute_custom_query", fake_execute_custom_query)

    result = await get_callback_agent_type(_build_ctx(), 5)

    assert result.callback_id == 5
    assert result.display_id == 2


@pytest.mark.asyncio
async def test_execute_with_validation_tasks_by_display_id(monkeypatch: pytest.MonkeyPatch):
    async def fake_validate_agent_type(ctx, callback_id, expected_agent_type):
        assert callback_id == 5
        assert expected_agent_type == "apollo"
        return CallbackAgentInfo(
            callback_id=5,
            display_id=2,
            agent_type="apollo",
            active=True,
        )

    async def fake_execute_task(ctx, callback_id, command_name, parameters=None, timeout=60):
        assert callback_id == 2
        assert command_name == "whoami"
        return ExecuteTaskResponse(
            task_id=101,
            task_display_id=7,
            status=TaskStatus.COMPLETED,
            command="whoami",
            agent_type="apollo",
            callback_id=2,
            output=[],
            error=None,
        )

    monkeypatch.setattr(
        "mythicmcp.plugins.executor.validate_agent_type",
        fake_validate_agent_type,
    )
    monkeypatch.setattr(
        "mythicmcp.plugins.executor.execute_task",
        fake_execute_task,
    )

    result = await execute_with_validation(
        ctx=_build_ctx(),
        callback_id=5,
        expected_agent_type="apollo",
        command_name="whoami",
        parameters={},
        timeout=30,
    )

    assert result.success is True
    assert result.task_id == 101
    assert result.task_display_id == 7


@pytest.mark.asyncio
async def test_execute_with_validation_returns_display_id_for_task_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_validate_agent_type(ctx, callback_id, expected_agent_type):
        return CallbackAgentInfo(
            callback_id=5,
            display_id=2,
            agent_type="apollo",
            active=True,
        )

    async def fake_execute_task(ctx, callback_id, command_name, parameters=None, timeout=60):
        return ExecuteTaskResponse(
            task_id=101,
            task_display_id=17,
            status=TaskStatus.ERROR,
            command="whoami",
            agent_type="apollo",
            callback_id=2,
            output=[],
            error="Task execution failed",
        )

    monkeypatch.setattr(
        "mythicmcp.plugins.executor.validate_agent_type",
        fake_validate_agent_type,
    )
    monkeypatch.setattr(
        "mythicmcp.plugins.executor.execute_task",
        fake_execute_task,
    )

    result = await execute_with_validation(
        ctx=_build_ctx(),
        callback_id=5,
        expected_agent_type="apollo",
        command_name="whoami",
        parameters={},
        timeout=30,
    )

    assert result.success is False
    assert result.task_id == 101
    assert result.task_display_id == 17


@pytest.mark.asyncio
async def test_execute_with_validation_leaves_display_id_empty_before_task_creation(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_validate_agent_type(ctx, callback_id, expected_agent_type):
        raise CallbackNotFoundError(callback_id)

    monkeypatch.setattr(
        "mythicmcp.plugins.executor.validate_agent_type",
        fake_validate_agent_type,
    )

    result = await execute_with_validation(
        ctx=_build_ctx(),
        callback_id=404,
        expected_agent_type="apollo",
        command_name="whoami",
        parameters={},
        timeout=30,
    )

    assert result.success is False
    assert result.task_id is None
    assert result.task_display_id is None


@pytest.mark.asyncio
async def test_execute_task_sends_empty_string_for_no_arg_commands(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict = {}

    async def fake_issue_task(*args, **kwargs):
        captured.update(kwargs)
        return {
            "id": 101,
            "display_id": 15,
            "status": "completed",
            "callback": {"payload": {"payloadtype": {"name": "apollo"}}},
        }

    async def fake_get_task_output(*args, **kwargs):
        return []

    monkeypatch.setattr("mythic.mythic.issue_task", fake_issue_task)
    monkeypatch.setattr(
        "mythicmcp.plugins.executor.get_task_output",
        fake_get_task_output,
    )

    result = await execute_task(
        ctx=_build_ctx(),
        callback_id=2,
        command_name="whoami",
        parameters={},
        timeout=30,
    )

    assert captured["parameters"] == ""
    assert result.task_id == 101


@pytest.mark.asyncio
async def test_execute_task_decodes_response_text_output(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_issue_task(*args, **kwargs):
        return {
            "id": 101,
            "display_id": 15,
            "status": "completed",
            "callback": {"payload": {"payloadtype": {"name": "apollo"}}},
        }

    async def fake_get_all_task_output_by_id(*args, **kwargs):
        return [
            {"id": 201, "response_text": "bGluZSBvbmU=", "timestamp": "2026-04-21T00:00:00Z"}
        ]

    monkeypatch.setattr("mythic.mythic.issue_task", fake_issue_task)
    monkeypatch.setattr(
        "mythic.mythic.get_all_task_output_by_id",
        fake_get_all_task_output_by_id,
    )

    result = await execute_task(
        ctx=_build_ctx(),
        callback_id=2,
        command_name="shell",
        parameters={"command": "whoami"},
        timeout=30,
    )

    assert result.output[0].response == "line one"
