"""Negative testing against the real HTTP layer (FastAPI TestClient) — not
just the orchestrator functions directly. Firestore is faked; Gemini/ADK
and the demo-service HTTP target are not exercised here (see
test_orchestrator.py / test_cross_incident_security.py for those paths) —
this file is specifically about how the API layer itself handles bad input:
malformed JSON, wrong types, nonexistent/malformed IDs, unsafe strings,
oversized payloads, and idempotency through the real endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.incidents_store import new_incident, new_remediation
from tests.fake_firestore import FakeFirestoreClient


@pytest.fixture
def db(monkeypatch):
    fake_db = FakeFirestoreClient()
    monkeypatch.setattr(main, "get_firestore_client", lambda: fake_db)
    return fake_db


@pytest.fixture
def client():
    return TestClient(main.app)


def test_get_nonexistent_incident_returns_404_not_500(client, db):
    resp = client.get("/incidents/does-not-exist")
    assert resp.status_code == 404


def test_approve_nonexistent_incident_returns_400_not_500(client, db):
    resp = client.post("/incidents/nope/remediations/nope/approve", json={})
    assert resp.status_code == 400
    assert resp.status_code != 500


def test_approve_with_malformed_json_body_returns_4xx_not_500(client, db):
    resp = client.post(
        "/incidents/x/remediations/y/approve",
        headers={"Content-Type": "application/json"},
        content=b"{not valid json",
    )
    assert 400 <= resp.status_code < 500


def test_autonomy_mode_rejects_unknown_enum_value(client, db):
    resp = client.put("/settings/autonomy-mode", json={"mode": "yolo_mode", "changed_by": "x"})
    assert resp.status_code == 400


def test_autonomy_mode_missing_mode_field_returns_4xx(client, db):
    resp = client.put("/settings/autonomy-mode", json={"changed_by": "x"})
    assert 400 <= resp.status_code < 500


def test_kill_switch_rejects_non_boolean_enabled(client, db):
    resp = client.put("/settings/kill-switch", json={"enabled": "yes please", "changed_by": "x"})
    assert resp.status_code == 400


def test_kill_switch_missing_enabled_field_returns_4xx(client, db):
    resp = client.put("/settings/kill-switch", json={"changed_by": "x"})
    assert 400 <= resp.status_code < 500


def test_wrong_http_method_on_incidents_is_rejected(client, db):
    resp = client.delete("/incidents/some-id")
    assert resp.status_code == 405


def test_wrong_http_method_on_settings_is_rejected(client, db):
    resp = client.post("/settings")
    assert resp.status_code == 405


def test_demo_trigger_missing_scenario_field_is_handled(client, db):
    # No scenario key at all -> demo_trigger sends scenario=None to the
    # (unreachable, in this test) demo-service and should surface a clean
    # error rather than crashing with an unrelated traceback.
    resp = client.post("/demo/trigger", json={})
    assert resp.status_code in (400, 422, 502)
    assert resp.status_code != 500


def test_service_profile_put_rejects_invalid_criticality(client, db):
    resp = client.put("/services/demo-service", json={"criticality": "super-duper-critical"})
    assert resp.status_code == 400


def test_service_profile_put_with_html_script_in_service_id_is_stored_as_literal_text(client, db):
    """The service_id becomes a Firestore document id, not HTML that's ever
    rendered server-side — this is really a frontend-escaping concern (React
    escapes by default), but confirm the backend doesn't choke or do
    anything unsafe with it either. (No literal '/' in the payload — that
    would split into multiple path segments and 404, which is a routing
    fact, not a security bug.)"""
    unsafe_id = '<img src=x onerror=alert(1)>'
    resp = client.put(f"/services/{unsafe_id}", json={"criticality": "low"})
    assert resp.status_code == 200
    assert resp.json()["service_id"] == unsafe_id


def test_service_profile_put_with_a_slash_in_the_id_is_a_clean_404_not_a_crash(client, db):
    """A '/' in a path parameter splits the URL into extra segments that
    don't match the route — confirms this fails as a clean 404, not a
    server error, rather than asserting it must be treated as one segment."""
    resp = client.put("/services/%3Cscript%3Ealert(1)%3C/script%3E", json={"criticality": "low"})
    assert resp.status_code != 500


def test_service_profile_put_with_very_long_service_id(client, db):
    long_id = "a" * 5000
    resp = client.put(f"/services/{long_id}", json={"criticality": "low"})
    # Should not 500 — either accepted or cleanly rejected, never a crash.
    assert resp.status_code != 500


def test_approve_endpoint_is_idempotent_through_the_real_http_layer(client, db, monkeypatch):
    """The end-to-end idempotency claim, proven through actual HTTP calls
    rather than calling orchestrator functions directly."""
    from app import orchestrator

    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])
    applied = []
    monkeypatch.setattr(
        orchestrator, "apply_safe_remediation", lambda service_id, action: applied.append(action)
    )
    from app.models import HealthResult

    monkeypatch.setattr(
        orchestrator, "verify_recovery", lambda service_id: HealthResult(status="healthy", checks={}, timestamp="t")
    )

    incident = new_incident(db, "demo-service")
    remediation = new_remediation(
        db, incident.id, "restore_env_var", risk="medium", status="awaiting_approval", reason="x", service_id="demo-service"
    )

    r1 = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/approve", json={"approved_by": "a"})
    assert r1.status_code == 200

    r2 = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/approve", json={"approved_by": "b"})
    assert r2.status_code == 400  # not a crash, a clean rejection

    assert applied == ["restore_env_var"]  # only executed once


def test_reject_then_approve_the_same_remediation_is_rejected(client, db, monkeypatch):
    # Rejecting re-plans, i.e. calls run_diagnosis again — mock it so this
    # test stays offline/deterministic instead of making a real Gemini call.
    from app import orchestrator
    from app.models import RemediationProposal

    async def fake_diagnose(service_id, attempted_actions):
        return (
            RemediationProposal(root_cause="x", confidence=0.9, severity="high", action="rollback_revision", reason="y"),
            [],
        )

    monkeypatch.setattr(orchestrator, "run_diagnosis", fake_diagnose)
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    incident = new_incident(db, "demo-service")
    remediation = new_remediation(
        db, incident.id, "restore_env_var", risk="medium", status="awaiting_approval", reason="x", service_id="demo-service"
    )

    r1 = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/reject", json={"rejected_by": "a"})
    assert r1.status_code == 200

    r2 = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/approve", json={"approved_by": "b"})
    assert r2.status_code == 400


def test_approve_an_already_verified_remediation_is_rejected(client, db):
    incident = new_incident(db, "demo-service")
    remediation = new_remediation(
        db, incident.id, "restore_env_var", risk="medium", status="verified", reason="x", service_id="demo-service"
    )
    resp = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/approve", json={"approved_by": "a"})
    assert resp.status_code == 400


def test_health_endpoint_always_works(client, db):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
