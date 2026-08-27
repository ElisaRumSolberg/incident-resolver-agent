from dataclasses import dataclass

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from app.agent.prompts import AGENT_INSTRUCTION, previous_attempts_context
from app.agent.tools import (
    extract_error_patterns,
    inspect_service_config,
    read_recent_logs,
)
from app.config import settings
from app.models import RemediationProposal

VALID_ACTIONS = {
    "retry_service",
    "rerun_health_check",
    "gather_logs",
    "restore_env_var",
    "rollback_revision",
    "fix_dependency_config",
    # Deliberately NOT in app.agent.safety.ACTION_RISK — the agent is allowed
    # to name this as a diagnosis (it's a legitimate tool argument, not a
    # typo/hallucination), but the safety whitelist in orchestrator.py has no
    # entry for it, so it is always blocked and escalated to a human rather
    # than auto/approve-executed. This is what makes the "blocked" safety
    # tier reachable instead of dead code.
    "rotate_credentials",
}


class AgentPipelineError(RuntimeError):
    """Raised when the agent did not complete the diagnosis sequence."""


@dataclass
class _PipelineState:
    proposal: RemediationProposal | None = None
    tool_calls: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


def _build_tools(service_id: str, attempted_actions: list[str], state: _PipelineState) -> list[FunctionTool]:
    def read_recent_logs_tool(limit: int = 50) -> dict:
        """Reads recent log entries from the service. Returns a list of
        {timestamp, level, message} entries, most recent last."""
        state.tool_calls.append("read_recent_logs")
        logs = read_recent_logs(service_id, limit=limit)
        state.__dict__["_logs"] = logs
        return {"logs": [log.model_dump() for log in logs]}

    def extract_error_patterns_tool() -> dict:
        """Groups the logs already read via read_recent_logs_tool into
        recurring error/warning patterns with counts and confidence.
        Call read_recent_logs_tool first."""
        state.tool_calls.append("extract_error_patterns")
        logs = state.__dict__.get("_logs")
        if not logs:
            return {"error": "call read_recent_logs_tool first"}
        patterns = extract_error_patterns(logs)
        return {"patterns": [p.model_dump() for p in patterns]}

    def inspect_service_config_tool() -> dict:
        """Returns safe, non-secret configuration metadata for the service
        (e.g. whether required config values are set, current revision)."""
        state.tool_calls.append("inspect_service_config")
        snapshot = inspect_service_config(service_id)
        return snapshot.model_dump()

    def propose_remediation_tool(
        root_cause: str, confidence: float, severity: str, action: str, reason: str
    ) -> dict:
        """Records your final diagnosis and proposed remediation. Call this
        exactly once, after investigating with the other tools.

        Args:
            root_cause: the specific root cause you identified, grounded in evidence.
            confidence: your confidence in this diagnosis, 0 to 1.
            severity: one of low, medium, high, critical.
            action: one of retry_service, rerun_health_check, gather_logs,
                restore_env_var, rollback_revision, fix_dependency_config,
                rotate_credentials.
            reason: why this action addresses the root cause you found.
        """
        if action not in VALID_ACTIONS:
            return {
                "error": f"'{action}' is not a known action. Choose one of: "
                f"{', '.join(sorted(VALID_ACTIONS))}"
            }
        if action in attempted_actions:
            # Code-enforced, not just a prompt instruction: a failed action
            # cannot be silently re-proposed just because the model ignored
            # the "don't repeat this" guidance in the prompt.
            remaining = sorted(VALID_ACTIONS - set(attempted_actions))
            return {
                "error": f"'{action}' was already tried for this incident and did not resolve it. "
                f"Propose a different action. Remaining untried options: {', '.join(remaining) or '(none)'}"
            }
        state.tool_calls.append("propose_remediation")
        state.proposal = RemediationProposal(
            root_cause=root_cause,
            confidence=confidence,
            severity=severity,  # type: ignore[arg-type]
            action=action,
            reason=reason,
        )
        return {"recorded": True}

    return [
        FunctionTool(read_recent_logs_tool),
        FunctionTool(extract_error_patterns_tool),
        FunctionTool(inspect_service_config_tool),
        FunctionTool(propose_remediation_tool),
    ]


async def _run_once(service_id: str, attempted_actions: list[str]) -> tuple[RemediationProposal, list[str]]:
    state = _PipelineState()
    agent = LlmAgent(
        name="incident_resolver_agent",
        model=settings.gemini_model,
        instruction=AGENT_INSTRUCTION + previous_attempts_context(attempted_actions),
        tools=_build_tools(service_id, attempted_actions, state),
    )
    runner = InMemoryRunner(agent=agent, app_name="incident_resolver_agent")
    session = await runner.session_service.create_session(
        app_name="incident_resolver_agent", user_id="api"
    )

    content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=f"Service '{service_id}' is currently unhealthy. Investigate and diagnose it."
            )
        ],
    )
    async for _event in runner.run_async(user_id="api", session_id=session.id, new_message=content):
        pass

    if state.proposal is None:
        raise AgentPipelineError("Agent did not complete the diagnosis/propose_remediation sequence.")

    return state.proposal, state.tool_calls


async def run_diagnosis(
    service_id: str, attempted_actions: list[str] | None = None
) -> tuple[RemediationProposal, list[str]]:
    """Runs the diagnosis agent once, retrying once on failure. Returns the
    proposal plus the ordered list of tool names the agent actually called,
    for the evidence/audit trail."""
    attempted = attempted_actions or []
    try:
        return await _run_once(service_id, attempted)
    except Exception:
        return await _run_once(service_id, attempted)
