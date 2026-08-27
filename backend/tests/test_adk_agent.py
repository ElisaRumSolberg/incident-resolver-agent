"""Tests for the ADK tool-level enforcement in adk_agent.py — specifically
that a failed action cannot be silently re-proposed. This is code-level
enforcement (not just a prompt instruction), tested by calling the built
FunctionTool's underlying function directly, without spinning up a real
LlmAgent/Gemini session."""

from app.agent.adk_agent import VALID_ACTIONS, _build_tools, _PipelineState


def _get_tool(tools, name: str):
    return next(t for t in tools if t.func.__name__ == name)


def test_propose_remediation_rejects_an_already_attempted_action():
    state = _PipelineState()
    tools = _build_tools("demo-service", ["retry_service"], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence=0.9, severity="high", action="retry_service", reason="y"
    )

    assert "error" in result
    assert "already tried" in result["error"]
    assert state.proposal is None


def test_propose_remediation_accepts_an_untried_action():
    state = _PipelineState()
    tools = _build_tools("demo-service", ["retry_service"], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence=0.9, severity="high", action="rollback_revision", reason="y"
    )

    assert result == {"recorded": True}
    assert state.proposal is not None
    assert state.proposal.action == "rollback_revision"
    assert "propose_remediation" in state.tool_calls


def test_propose_remediation_still_rejects_unknown_actions():
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence=0.9, severity="high", action="delete_database", reason="y"
    )

    assert "error" in result
    assert state.proposal is None


def test_error_message_lists_remaining_untried_valid_actions():
    state = _PipelineState()
    tools = _build_tools("demo-service", ["retry_service", "rerun_health_check"], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence=0.9, severity="high", action="retry_service", reason="y"
    )

    for remaining_action in VALID_ACTIONS - {"retry_service", "rerun_health_check"}:
        assert remaining_action in result["error"]
