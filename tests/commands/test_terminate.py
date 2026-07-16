"""Unit tests for the terminate command module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from devbox.cli_lambda.contracts import CliRequestEnvelope
from devbox.cli_protocol import CliAction
from devbox.commands.terminate import (
    build_terminate_payload,
    handle_terminate_action,
    run_terminate_command,
    validate_terminate_payload,
)


def make_terminate_envelope(
    identifier: str = "i-123",
    param_prefix: str = "/devbox",
) -> CliRequestEnvelope:
    return CliRequestEnvelope(
        version="v1",
        action=CliAction.TERMINATE,
        request_id="req-123",
        param_prefix=param_prefix,
        payload={"identifier": identifier},
    )


def test_build_terminate_payload_uses_identifier_field() -> None:
    assert build_terminate_payload("i-123") == {"identifier": "i-123"}


@patch("devbox.commands.terminate.invoke_action")
def test_run_terminate_command_fetches_and_renders_result(mock_invoke_action) -> None:
    mock_invoke_action.return_value = {
        "instance_id": "i-123",
        "project": "demo",
    }
    console = MagicMock()

    run_terminate_command("demo", "/devbox", console=console)

    mock_invoke_action.assert_called_once_with(
        action=CliAction.TERMINATE,
        payload={"identifier": "demo"},
        param_prefix="/devbox",
        console=console,
    )
    console.print_success.assert_called_once_with(
        "Terminating instance i-123 (project: demo)."
    )


def test_validate_terminate_payload_rejects_non_string_identifier() -> None:
    with pytest.raises(ValueError, match="must be a non-empty string"):
        validate_terminate_payload({"identifier": 123})


def test_validate_terminate_payload_rejects_empty_identifier() -> None:
    with pytest.raises(ValueError, match="must be a non-empty string"):
        validate_terminate_payload({"identifier": ""})


@patch("devbox.commands.terminate.DevBoxManager")
def test_handle_terminate_action_reuses_devbox_manager(mock_manager_class) -> None:
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    mock_manager.terminate_instance.return_value = {
        "instance_id": "i-123",
        "project": "demo",
    }

    events = handle_terminate_action(
        make_terminate_envelope(identifier="demo", param_prefix="/custom/devbox")
    )

    mock_manager_class.assert_called_once_with(prefix="custom/devbox")
    mock_manager.terminate_instance.assert_called_once_with("demo")
    assert events[0] == {
        "type": "result",
        "action": "terminate",
        "message": "Termination request accepted",
        "data": {"instance_id": "i-123", "project": "demo"},
    }
    assert events[1] == {
        "type": "success",
        "action": "terminate",
        "message": "Terminate complete",
        "data": {},
    }
