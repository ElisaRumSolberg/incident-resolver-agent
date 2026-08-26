from app.incidents_store import get_active_incident_for_service, new_incident, update_incident
from tests.fake_firestore import FakeFirestoreClient


def test_get_active_incident_for_service_finds_in_progress_incident():
    db = FakeFirestoreClient()
    incident = new_incident(db, "demo-service")

    found = get_active_incident_for_service(db, "demo-service")

    assert found is not None
    assert found.id == incident.id


def test_get_active_incident_for_service_ignores_resolved_incidents():
    db = FakeFirestoreClient()
    incident = new_incident(db, "demo-service")
    update_incident(db, incident.id, status="resolved")

    found = get_active_incident_for_service(db, "demo-service")

    assert found is None


def test_get_active_incident_for_service_ignores_other_services():
    db = FakeFirestoreClient()
    new_incident(db, "other-service")

    found = get_active_incident_for_service(db, "demo-service")

    assert found is None
