"""Adversarial check: what happens when the current incident's root_cause is
too short/generic to tokenize into any words at all (e.g. "db", or an empty
string)? _jaccard already guards div-by-zero, but the service-id bonus alone
was enough to clear min_similarity even with zero textual relation to the
past incident — surfacing a misleadingly labeled "similar incident" that
isn't actually similar in any way but service."""

from app.agent.similarity import find_similar_incidents
from tests.fake_firestore import FakeFirestoreClient
from app.models import Incident


def _seed_past_incident(db, incident_id, service_id, root_cause, status="resolved"):
    inc = Incident(
        id=incident_id,
        service_id=service_id,
        status=status,
        started_at="2026-01-01T00:00:00+00:00",
        resolved_at="2026-01-01T00:05:00+00:00",
        root_cause=root_cause,
        attempted_actions=["restart_service"],
    )
    db.collection("incidents").document(incident_id).set(inc.model_dump())


def test_untokenizable_root_cause_does_not_falsely_match_same_service_incident():
    db = FakeFirestoreClient()
    _seed_past_incident(
        db, "past-1", "payment-api", "credential file corrupted after deploy rollback"
    )

    results = find_similar_incidents(
        db, root_cause="db", service_id="payment-api", exclude_incident_id="current"
    )

    assert results == [], (
        "A root_cause with no comparable words (\"db\" tokenizes to nothing) "
        "matched a completely unrelated past incident purely on the same-"
        "service bonus, mislabeling it as a similar incident with no actual "
        "textual basis."
    )


def test_empty_root_cause_returns_no_matches():
    db = FakeFirestoreClient()
    _seed_past_incident(db, "past-1", "payment-api", "missing environment variable")

    results = find_similar_incidents(
        db, root_cause="", service_id="payment-api", exclude_incident_id="current"
    )
    assert results == []
