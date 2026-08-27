"""Regression tests for a CRITICAL bug found in adversarial review:
approve_remediation/reject_remediation fetched the remediation by
remediation_id alone and never checked it actually belongs to the
incident_id in the URL. A caller could approve/reject ANY awaiting-approval
remediation from ANY incident by pairing it with an unrelated incident_id —
the action would then execute against the WRONG incident's service_id and
corrupt the WRONG incident's state.
"""

import pytest

from app import orchestrator
from app.incidents_store import new_incident
from app.models import RemediationProposal
from tests.fake_firestore import FakeFirestoreClient


def _proposal(action: str) -> RemediationProposal:
    return RemediationProposal(root_cause="x", confidence=0.9, severity="high", action=action, reason="y")


@pytest.mark.asyncio
async def test_cannot_approve_a_remediation_via_an_unrelated_incident_id(monkeypatch):
    applied = []
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append((service_id, action))
    )
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: __import__("app.models", fromlist=["HealthResult"]).HealthResult(status="healthy", checks={}, timestamp="2026-01-01T00:00:00Z"))

    db = FakeFirestoreClient()

    async def diagnose_a(service_id, attempted_actions):
        return _proposal("restore_env_var"), []

    monkeypatch.setattr(orchestrator, "run_diagnosis", diagnose_a)
    incident_a = new_incident(db, "payment-api")
    _, remediation_a = await orchestrator.investigate(db, incident_a)

    incident_b = new_incident(db, "notification-worker")

    # Attacker (or a buggy client) pairs incident B's id with incident A's
    # awaiting-approval remediation.
    with pytest.raises(ValueError, match="does not belong"):
        await orchestrator.approve_remediation(db, incident_b.id, remediation_a.id, approved_by="attacker")

    # Must not have executed anything against either service.
    assert applied == []
    from app.incidents_store import get_remediation

    still_pending = get_remediation(db, remediation_a.id)
    assert still_pending.status == "awaiting_approval"


@pytest.mark.asyncio
async def test_cannot_reject_a_remediation_via_an_unrelated_incident_id(monkeypatch):
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    db = FakeFirestoreClient()

    async def diagnose(service_id, attempted_actions):
        return _proposal("restore_env_var"), []

    monkeypatch.setattr(orchestrator, "run_diagnosis", diagnose)
    incident_a = new_incident(db, "payment-api")
    _, remediation_a = await orchestrator.investigate(db, incident_a)
    incident_b = new_incident(db, "notification-worker")

    with pytest.raises(ValueError, match="does not belong"):
        await orchestrator.reject_remediation(db, incident_b.id, remediation_a.id, rejected_by="attacker")

    from app.incidents_store import get_remediation

    still_pending = get_remediation(db, remediation_a.id)
    assert still_pending.status == "awaiting_approval"
    # incident_b must not have been touched at all
    from app.incidents_store import get_incident

    b_after = get_incident(db, incident_b.id)
    assert b_after.rejected_actions == []


@pytest.mark.asyncio
async def test_approve_nonexistent_remediation_id_fails_safely(monkeypatch):
    db = FakeFirestoreClient()
    incident = new_incident(db, "demo-service")
    with pytest.raises(ValueError, match="not found"):
        await orchestrator.approve_remediation(db, incident.id, "does-not-exist", approved_by="x")


@pytest.mark.asyncio
async def test_approve_nonexistent_incident_id_fails_safely(monkeypatch):
    db = FakeFirestoreClient()
    with pytest.raises(ValueError, match="not found"):
        await orchestrator.approve_remediation(db, "does-not-exist", "also-does-not-exist", approved_by="x")


@pytest.mark.asyncio
async def test_reject_nonexistent_ids_fails_safely():
    db = FakeFirestoreClient()
    with pytest.raises(ValueError, match="not found"):
        await orchestrator.reject_remediation(db, "nope", "nope", rejected_by="x")
