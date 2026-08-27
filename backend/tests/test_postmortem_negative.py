"""Negative testing for the postmortem endpoint — an unresolved incident,
missing incident, and one with no activity events must all fail safely or
degrade gracefully, never fabricate history."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.incidents_store import new_incident, update_incident
from tests.fake_firestore import FakeFirestoreClient


@pytest.fixture
def db(monkeypatch):
    fake_db = FakeFirestoreClient()
    monkeypatch.setattr(main, "get_firestore_client", lambda: fake_db)
    return fake_db


@pytest.fixture
def client():
    return TestClient(main.app)


def test_postmortem_for_nonexistent_incident_returns_404(client, db):
    resp = client.get("/incidents/does-not-exist/postmortem")
    assert resp.status_code == 404


def test_postmortem_for_unresolved_incident_is_rejected(client, db):
    incident = new_incident(db, "demo-service")  # status: investigating
    resp = client.get(f"/incidents/{incident.id}/postmortem")
    assert resp.status_code == 400


def test_postmortem_for_escalated_incident_is_also_rejected(client, db):
    """Only 'resolved' incidents get postmortems — an escalated one has no
    success to summarize, and the endpoint should say so rather than
    generating a postmortem that implies things went fine."""
    incident = new_incident(db, "demo-service")
    update_incident(db, incident.id, status="escalation_required")
    resp = client.get(f"/incidents/{incident.id}/postmortem")
    assert resp.status_code == 400


def test_postmortem_for_recommended_incident_is_rejected(client, db):
    incident = new_incident(db, "demo-service")
    update_incident(db, incident.id, status="recommended")
    resp = client.get(f"/incidents/{incident.id}/postmortem")
    assert resp.status_code == 400
