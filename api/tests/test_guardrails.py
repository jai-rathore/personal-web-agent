"""Tests for the guardrails pipeline."""
import pytest
from app.agent.guardrails import GuardrailError, validate_input, validate_tool_name


def test_valid_input_passes():
    validate_input("What is Jai's experience at Tesla?")


def test_empty_input_raises():
    with pytest.raises(GuardrailError):
        validate_input("")


def test_input_too_long_raises():
    with pytest.raises(GuardrailError):
        validate_input("x" * 2001)


@pytest.mark.parametrize("blocked", [
    "ignore previous instructions",
    "system prompt",
    "jailbreak",
    "<script>alert(1)</script>",
])
def test_blocked_strings_raise(blocked: str):
    with pytest.raises(GuardrailError):
        validate_input(blocked)


def test_allowed_tool_passes():
    validate_tool_name("schedule_calendly_meeting")
    validate_tool_name("get_contact_info")
    validate_tool_name("list_calendar_events")


def test_unknown_tool_raises():
    with pytest.raises(GuardrailError):
        validate_tool_name("run_shell_command")
