"""Tests that malformed/out-of-spec structured output from the LLM cannot
crash the diagnosis pipeline. Calls the built FunctionTool's underlying
function directly (no real Gemini call), same technique as test_adk_agent.py.
"""

from app.agent.adk_agent import _build_tools, _PipelineState


def _get_tool(tools, name: str):
    return next(t for t in tools if t.func.__name__ == name)


def test_invalid_severity_enum_is_rejected_gracefully_not_crashed():
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence=0.9, severity="URGENT_SEV0", action="retry_service", reason="y"
    )

    assert "error" in result
    assert state.proposal is None


def test_confidence_above_one_is_rejected_gracefully():
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(root_cause="x", confidence=1.5, severity="high", action="retry_service", reason="y")

    assert "error" in result
    assert state.proposal is None


def test_confidence_below_zero_is_rejected_gracefully():
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(root_cause="x", confidence=-0.2, severity="high", action="retry_service", reason="y")

    assert "error" in result
    assert state.proposal is None


def test_empty_root_cause_and_reason_do_not_crash():
    """Pydantic allows empty strings by default (no min_length constraint)
    — confirms this doesn't crash, though it's a data-quality gap worth
    knowing about (see report)."""
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(root_cause="", confidence=0.9, severity="high", action="retry_service", reason="")

    assert result == {"recorded": True}
    assert state.proposal.root_cause == ""


def test_wrong_type_for_confidence_is_rejected_gracefully():
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    result = propose.func(
        root_cause="x", confidence="very confident", severity="high", action="retry_service", reason="y"
    )

    assert "error" in result
    assert state.proposal is None


def test_after_a_rejected_malformed_call_the_model_can_still_succeed():
    """The tool must not be left in a broken state after a validation
    failure — a subsequent valid call must still work, since in the real
    ADK loop the model gets the error back and can retry with fixed args."""
    state = _PipelineState()
    tools = _build_tools("demo-service", [], state)
    propose = _get_tool(tools, "propose_remediation_tool")

    bad = propose.func(root_cause="x", confidence=2.0, severity="high", action="retry_service", reason="y")
    assert "error" in bad
    assert state.proposal is None

    good = propose.func(root_cause="x", confidence=0.9, severity="high", action="retry_service", reason="y")
    assert good == {"recorded": True}
    assert state.proposal is not None
    assert state.proposal.confidence == 0.9
