from unittest.mock import MagicMock

from app.agent.similarity import find_similar_incidents


def _fake_incident_snap(data: dict):
    snap = MagicMock()
    snap.to_dict.return_value = data
    return snap


def test_find_similar_incidents_ranks_by_overlap_and_service(monkeypatch):
    past = [
        _fake_incident_snap(
            {
                "id": "a",
                "status": "resolved",
                "service_id": "payment-api",
                "root_cause": "Database connection pool exhausted under high load",
                "attempted_actions": ["restart_service"],
            }
        ),
        _fake_incident_snap(
            {
                "id": "b",
                "status": "resolved",
                "service_id": "auth-service",
                "root_cause": "Revision crash-looping on startup due to bad config",
                "attempted_actions": ["rollback_revision"],
            }
        ),
    ]

    db = MagicMock()
    db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = past

    results = find_similar_incidents(
        db,
        root_cause="Database connection pool exhausted",
        service_id="payment-api",
        exclude_incident_id="current",
    )

    assert len(results) == 1
    assert results[0]["incident_id"] == "a"
    assert results[0]["action"] == "restart_service"
    assert 0 < results[0]["similarity"] <= 0.99


def test_find_similar_incidents_excludes_self_and_low_scores():
    past = [
        _fake_incident_snap(
            {"id": "current", "status": "resolved", "service_id": "x", "root_cause": "same", "attempted_actions": []}
        ),
        _fake_incident_snap(
            {
                "id": "unrelated",
                "status": "resolved",
                "service_id": "other",
                "root_cause": "completely different topic entirely",
                "attempted_actions": [],
            }
        ),
    ]
    db = MagicMock()
    db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = past

    results = find_similar_incidents(db, root_cause="missing env var issue", service_id="x", exclude_incident_id="current")
    assert results == []


def test_find_similar_incidents_includes_escalated_ones_marked_failed():
    past = [
        _fake_incident_snap(
            {
                "id": "a",
                "status": "escalation_required",
                "service_id": "payment-api",
                "root_cause": "Database connection pool exhausted under high load",
                "attempted_actions": ["retry_service", "rerun_health_check"],
            }
        ),
    ]
    db = MagicMock()
    db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = past

    results = find_similar_incidents(
        db, root_cause="Database connection pool exhausted", service_id="payment-api", exclude_incident_id="current"
    )

    assert len(results) == 1
    assert results[0]["result"] == "failed"
    assert results[0]["action"] == "rerun_health_check"
