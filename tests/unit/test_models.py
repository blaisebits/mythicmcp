"""Unit tests for mythicmcp.models module."""

from datetime import datetime, timezone

import pytest

from tests.lab_config import CALLBACK_ALT_IP, CALLBACK_EXTERNAL_IP, CALLBACK_INTERNAL_IP
from mythicmcp.models import (
    CallbackDetail,
    CallbackSummary,
    CheckConnectionErrorResponse,
    CheckConnectionResponse,
    GetCallbackResponse,
    GetOperationResponse,
    ListCallbacksResponse,
    OperationInfo,
    OperatorInfo,
)


class TestCallbackSummary:
    """Tests for CallbackSummary model."""

    def test_create_callback_summary(self):
        """CallbackSummary can be created with required fields."""
        cb = CallbackSummary(
            callback_id=1,
            display_id=1,
            hostname="WORKSTATION-01",
            username="john.doe",
            agent_type="apollo",
            os="Windows 10",
            internal_ip=CALLBACK_INTERNAL_IP,
            integrity_level=3,
            process_name="explorer.exe",
            active=True,
        )
        assert cb.callback_id == 1
        assert cb.hostname == "WORKSTATION-01"
        assert cb.agent_type == "apollo"
        assert cb.active is True


class TestCallbackDetail:
    """Tests for CallbackDetail model."""

    def test_create_callback_detail(self):
        """CallbackDetail can be created with all fields."""
        cb = CallbackDetail(
            callback_id=1,
            display_id=1,
            hostname="WORKSTATION-01",
            username="john.doe",
            domain="CORP",
            internal_ip=CALLBACK_INTERNAL_IP,
            external_ip=CALLBACK_EXTERNAL_IP,
            os="Windows 10",
            architecture="x64",
            process_id=1234,
            process_name="explorer.exe",
            integrity_level=3,
            agent_type="apollo",
            description="Initial callback",
            active=True,
        )
        assert cb.domain == "CORP"
        assert cb.external_ip == CALLBACK_EXTERNAL_IP
        assert cb.architecture == "x64"
        assert cb.process_id == 1234

    def test_callback_detail_defaults(self):
        """CallbackDetail has sensible defaults for optional fields."""
        cb = CallbackDetail(
            callback_id=1,
            display_id=1,
            hostname="HOST",
            username="user",
            internal_ip=CALLBACK_ALT_IP,
            os="Linux",
            process_id=100,
            process_name="bash",
            integrity_level=0,
            agent_type="poseidon",
            active=True,
        )
        assert cb.domain == ""
        assert cb.external_ip == ""
        assert cb.architecture == ""
        assert cb.description == ""


class TestListCallbacksResponse:
    """Tests for ListCallbacksResponse model."""

    def test_response_has_timestamp(self):
        """ListCallbacksResponse includes retrieved_at timestamp."""
        response = ListCallbacksResponse(callbacks=[], count=0)
        assert response.retrieved_at is not None
        assert isinstance(response.retrieved_at, datetime)
        assert response.retrieved_at.tzinfo == timezone.utc

    def test_response_with_callbacks(self):
        """ListCallbacksResponse can contain callbacks."""
        cb = CallbackSummary(
            callback_id=1,
            display_id=1,
            hostname="HOST",
            username="user",
            agent_type="apollo",
            os="Windows",
            internal_ip=CALLBACK_ALT_IP,
            integrity_level=2,
            process_name="cmd.exe",
            active=True,
        )
        response = ListCallbacksResponse(callbacks=[cb], count=1)
        assert len(response.callbacks) == 1
        assert response.count == 1


class TestGetCallbackResponse:
    """Tests for GetCallbackResponse model."""

    def test_response_has_timestamp(self):
        """GetCallbackResponse includes retrieved_at timestamp."""
        cb = CallbackDetail(
            callback_id=1,
            display_id=1,
            hostname="HOST",
            username="user",
            internal_ip=CALLBACK_ALT_IP,
            os="Windows",
            process_id=100,
            process_name="cmd.exe",
            integrity_level=2,
            agent_type="apollo",
            active=True,
        )
        response = GetCallbackResponse(callback=cb)
        assert response.retrieved_at is not None
        assert response.retrieved_at.tzinfo == timezone.utc


class TestOperationModels:
    """Tests for Operation-related models."""

    def test_operation_info(self):
        """OperationInfo can be created."""
        op = OperationInfo(
            id=1,
            name="Operation Sunrise",
            created_at=datetime(2026, 1, 20, 8, 0, 0, tzinfo=timezone.utc),
            complete=False,
        )
        assert op.name == "Operation Sunrise"
        assert op.complete is False

    def test_operator_info(self):
        """OperatorInfo can be created."""
        operator = OperatorInfo(username="admin", admin=True)
        assert operator.username == "admin"
        assert operator.admin is True

    def test_get_operation_response_has_timestamp(self):
        """GetOperationResponse includes retrieved_at timestamp."""
        op = OperationInfo(
            id=1,
            name="Test Op",
            created_at=datetime.now(timezone.utc),
            complete=False,
        )
        response = GetOperationResponse(operation=op, operators=[])
        assert response.retrieved_at is not None
        assert response.retrieved_at.tzinfo == timezone.utc


class TestConnectionModels:
    """Tests for Connection-related models."""

    def test_check_connection_success_response(self):
        """CheckConnectionResponse can indicate success."""
        from mythicmcp.models import OperationSummary

        response = CheckConnectionResponse(
            connected=True,
            server_url="https://mythic.local:7443",
            authenticated=True,
            current_operation="Operation Sunrise",
            accessible_operations=[
                OperationSummary(
                    id=1,
                    name="Operation Sunrise",
                    complete=False,
                    admin_username="alice",
                )
            ],
        )
        assert response.connected is True
        assert response.authenticated is True
        assert response.current_operation == "Operation Sunrise"
        assert response.accessible_operations[0].name == "Operation Sunrise"
        assert response.timestamp is not None

    def test_check_connection_success_no_operation(self):
        """CheckConnectionResponse can have no current operation."""
        response = CheckConnectionResponse(
            connected=True,
            server_url="https://mythic.local:7443",
            authenticated=True,
            current_operation=None,
        )
        assert response.current_operation is None
        assert response.accessible_operations == []

    def test_check_connection_error_response(self):
        """CheckConnectionErrorResponse can indicate failure."""
        response = CheckConnectionErrorResponse(
            error="Connection refused",
            error_type="connection_failed",
            server_url="https://mythic.local:7443",
        )
        assert response.connected is False
        assert response.error == "Connection refused"
        assert response.error_type == "connection_failed"
        assert response.timestamp is not None
