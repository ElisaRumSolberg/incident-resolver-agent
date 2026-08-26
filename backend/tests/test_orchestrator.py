"""Orchestrator behavior tests — the safety gate, the approval flow, and the
re-plan / escalation loop. Firestore and the ADK/Gemini call are both faked
so these run offline and deterministically.

These encode the four claims the whole project's safety pitch rests on:
  1. LOW risk executes without a human.
  2. MEDIUM risk never executes until a human approves.
  3. A verify failure triggers re-planning with a different action.
  4. Repeated failure escalates to a human instead of looping forever.
Plus the idempotency guarantee: approving/rejecting an already-decided
remediation is rejected, not silently re-applied.
"""

import pytest

from app import orchestrator
from app.incidents_store import new_incident
from app.models import HealthResult, RemediationProposal
from tests.fake_firestore import FakeFirestoreClient


@pytest.fixture
def db():
    return FakeFirestoreClient()


def _proposal(action: str, root_cause: str = "something broke") -> RemediationProposal:
    return RemediationProposal(
        root_cause=root_cause, confidence=0.9, severity="high", action=action, reason="because logs said so"
    )


def _healthy() -> HealthResult:
    return HealthResult(status="healthy", checks={}, timestamp="2026-01-01T00:00:00Z")


def _diagnose_fixed(action: str):
    """run_diagnosis is `async def` — the fake must be awaitable too."""

    async def fake(service_id, attempted_actions):
        return _proposal(action)

    return fake


def _unhealthy() -> HealthResult:
    return HealthResult(status="unhealthy", checks={}, timestamp="2026-01-01T00:00:00Z")


@pytest.mark.asyncio
async def test_low_risk_auto_executes_without_approval(db, monkeypatch):
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("retry_service"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    result_incident, remediation = await orchestrator.investigate(db, incident)

    assert applied == ["retry_service"]  # executed without any approve() call
    assert remediation.status == "verified"
    assert result_incident.status == "resolved"


@pytest.mark.asyncio
async def test_medium_risk_never_executes_before_approval(db, monkeypatch):
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("restore_env_var"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    result_incident, remediation = await orchestrator.investigate(db, incident)

    assert applied == []  # MUST NOT have executed yet
    assert remediation.status == "awaiting_approval"
    assert result_incident.status == "awaiting_approval"


@pytest.mark.asyncio
async def test_approve_then_executes_and_resolves(db, monkeypatch):
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("rollback_revision"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    _, remediation = await orchestrator.investigate(db, incident)

    result_incident, result_remediation = await orchestrator.approve_remediation(db, incident.id, remediation.id)

    assert applied == ["rollback_revision"]
    assert result_remediation.status == "verified"
    assert result_incident.status == "resolved"


@pytest.mark.asyncio
async def test_double_approve_is_rejected_not_double_applied(db, monkeypatch):
    """Idempotency: approving an already-decided remediation a second time
    must not apply the action twice."""
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("rollback_revision"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    _, remediation = await orchestrator.investigate(db, incident)
    await orchestrator.approve_remediation(db, incident.id, remediation.id)

    with pytest.raises(ValueError):
        await orchestrator.approve_remediation(db, incident.id, remediation.id)

    assert applied == ["rollback_revision"]  # still only once


@pytest.mark.asyncio
async def test_reject_never_applies_the_action(db, monkeypatch):
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("fix_dependency_config"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    _, remediation = await orchestrator.investigate(db, incident)
    result_incident, result_remediation = await orchestrator.reject_remediation(db, incident.id, remediation.id)

    assert applied == []
    # reject_remediation re-plans, so the return value is the NEW proposal —
    # the original rejected one has to be looked up separately to confirm
    # it really was marked rejected and not silently left/re-used.
    from app.incidents_store import get_remediation

    original = get_remediation(db, remediation.id)
    assert original.status == "rejected"
    assert result_remediation.id != remediation.id
    # rejection re-plans (a second diagnosis runs) rather than leaving it stuck
    assert result_incident.status in ("awaiting_approval", "investigating", "escalation_required")


@pytest.mark.asyncio
async def test_failed_verification_triggers_replan_with_a_different_action(db, monkeypatch):
    calls = {"n": 0}
    proposals = ["retry_service", "rerun_health_check"]

    async def fake_diagnose(service_id, attempted_actions):
        action = proposals[calls["n"]]
        calls["n"] += 1
        assert action not in attempted_actions  # the re-plan must not repeat a failed action
        return _proposal(action)

    healths = [_unhealthy(), _healthy()]

    def fake_verify(service_id):
        return healths.pop(0)

    monkeypatch.setattr(orchestrator, "run_diagnosis", fake_diagnose)
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(orchestrator, "apply_safe_remediation", lambda service_id, action: None)
    monkeypatch.setattr(orchestrator, "verify_recovery", fake_verify)

    incident = new_incident(db, "demo-service")
    result_incident, _ = await orchestrator.investigate(db, incident)

    assert calls["n"] == 2  # diagnosed twice: once, failed, re-planned
    assert result_incident.status == "resolved"
    assert result_incident.attempted_actions == ["retry_service", "rerun_health_check"]


@pytest.mark.asyncio
async def test_repeated_failure_escalates_after_max_attempts(db, monkeypatch):
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("retry_service"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(orchestrator, "apply_safe_remediation", lambda service_id, action: None)
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _unhealthy())  # never recovers

    incident = new_incident(db, "demo-service")
    result_incident, _ = await orchestrator.investigate(db, incident)

    assert result_incident.status == "escalation_required"
    assert len(result_incident.attempted_actions) == orchestrator.MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_dangerous_action_is_blocked_and_never_executed(db, monkeypatch):
    """The headline safety claim: an action outside the whitelist (e.g. the
    agent legitimately diagnosing that credentials must be rotated) must be
    escalated, never auto/approve-executed — regression test for the finding
    that this path used to be unreachable (VALID_ACTIONS == ACTION_RISK.keys())."""
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("rotate_credentials"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    result_incident, remediation = await orchestrator.investigate(db, incident)

    assert applied == []
    assert remediation.status == "blocked"
    assert remediation.risk == "high"
    assert result_incident.status == "escalation_required"


@pytest.mark.asyncio
async def test_apply_failure_is_a_controlled_failed_attempt_not_a_crash(db, monkeypatch):
    """Regression test: apply_safe_remediation raising (e.g. the target
    service returning 400 because a concurrent incident already resolved it)
    must not propagate as an unhandled exception."""

    def boom(service_id, action):
        raise RuntimeError("target unreachable")

    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("retry_service"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(orchestrator, "apply_safe_remediation", boom)
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    # Must not raise.
    result_incident, _ = await orchestrator.investigate(db, incident)

    assert result_incident.status == "escalation_required"
    assert result_incident.attempted_actions == ["retry_service"] * orchestrator.MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_no_effect_apply_is_not_reported_as_success(db, monkeypatch):
    """Regression test: if the target reports the action had no effect
    (its failure state already changed, e.g. fixed by someone else), that
    must not be reported as a successful resolution."""
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("retry_service"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: {"status": "no_effect"}
    )
    # Health check reports healthy even though THIS incident's action did nothing.
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    result_incident, remediation = await orchestrator.investigate(db, incident)

    assert remediation.status == "failed"
    assert result_incident.status != "resolved"


@pytest.mark.asyncio
async def test_three_rejections_escalate_without_any_real_attempt(db, monkeypatch):
    """Regression test: rejecting proposals must not be counted the same as
    trying and failing them — rejected_actions and attempted_actions must
    stay separate, and escalation after 3 rejects must not claim 3 fixes
    were tried."""
    applied = []
    monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnose_fixed("restore_env_var"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: _healthy())

    incident = new_incident(db, "demo-service")
    _, remediation = await orchestrator.investigate(db, incident)

    result_incident = None
    for _ in range(orchestrator.MAX_ATTEMPTS):
        result_incident, remediation = await orchestrator.reject_remediation(db, incident.id, remediation.id)

    assert applied == []  # nothing was ever actually tried
    assert result_incident.status == "escalation_required"
    assert result_incident.attempted_actions == []
    assert len(result_incident.rejected_actions) == orchestrator.MAX_ATTEMPTS
