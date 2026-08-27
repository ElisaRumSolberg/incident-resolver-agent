"""Regression tests for a real bug found while auditing what happens at data
volumes beyond the various `.limit(N)` calls sprinkled through analytics.py,
similarity.py, and incidents_store.py: none of them called `.order_by()`
first, so once a collection grew past the limit, the query returned an
arbitrary/undefined-order subset instead of the most recent N documents.

For `list_remediations_for_service` (used by the safety rate limiter) this
is not just a cosmetic stats bug — it means the rate limiter could silently
evaluate against a subset that excludes the most recent executions, which
is exactly backwards for a safety control.
"""

from datetime import datetime, timedelta, timezone

from app.incidents_store import list_remediations_for_service
from app.models import RemediationRecord
from tests.fake_firestore import FakeFirestoreClient


def _iso(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


def test_rate_limit_query_still_sees_the_most_recent_execution_past_the_limit():
    """Insert more remediations for OTHER services than the internal limit,
    all older, then one very recent remediation for the service under test.
    Without ordering by recency before truncating, the recent one could be
    dropped from the window entirely — silently defeating the rate limit."""
    db = FakeFirestoreClient()

    # Fill the collection with old noise from unrelated services, more than
    # the default limit=500 the rate limiter's query uses.
    for i in range(510):
        record = RemediationRecord(
            id=f"old-{i}",
            incident_id=f"inc-{i}",
            service_id="other-service",
            action="retry_service",
            risk="low",
            status="verified",
            created_at=_iso(minutes_ago=1000 + i),
            executed_at=_iso(minutes_ago=1000 + i),
        )
        db.collection("remediations").document(record.id).set(record.model_dump())

    # The one execution that actually matters for this test: recent, for the
    # service under test.
    recent = RemediationRecord(
        id="recent-1",
        incident_id="inc-target",
        service_id="target-service",
        action="restore_env_var",
        risk="medium",
        status="applied",
        created_at=_iso(minutes_ago=1),
        executed_at=_iso(minutes_ago=1),
    )
    db.collection("remediations").document(recent.id).set(recent.model_dump())

    results = list_remediations_for_service(db, "target-service", action="restore_env_var")

    assert any(r.id == "recent-1" for r in results), (
        "The most recent remediation for the target service was dropped from "
        "the rate-limit query once the collection exceeded the query limit — "
        "the safety rate limiter must never lose visibility into recent "
        "executions."
    )


def test_overview_active_count_still_sees_a_recent_incident_past_the_limit():
    from app.analytics import compute_overview
    from app.models import Incident

    db = FakeFirestoreClient()
    for i in range(510):
        inc = Incident(
            id=f"old-{i}",
            service_id="noise-service",
            status="resolved",
            started_at=_iso(minutes_ago=2000 + i),
            resolved_at=_iso(minutes_ago=1999 + i),
        )
        db.collection("incidents").document(inc.id).set(inc.model_dump())

    active = Incident(
        id="recent-active",
        service_id="target-service",
        status="investigating",
        started_at=_iso(minutes_ago=1),
    )
    db.collection("incidents").document(active.id).set(active.model_dump())

    overview = compute_overview(db)
    assert overview["active_count"] == 1, (
        "A currently-active incident was excluded from the overview once the "
        "incidents collection exceeded the query limit, because the query "
        "had no ordering to prefer recent documents before truncating."
    )
