from app.agent.policy import evaluate_policy
from app.incidents_store import new_remediation
from app.models import ServiceProfile
from app.settings_store import set_autonomy_mode, set_kill_switch, upsert_service_profile
from tests.fake_firestore import FakeFirestoreClient


def test_default_mode_auto_executes_low_risk():
    db = FakeFirestoreClient()
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "auto_execute"
    assert evaluation.risk == "low"


def test_default_mode_requires_approval_for_medium_risk():
    db = FakeFirestoreClient()
    evaluation = evaluate_policy(db, "demo-service", "restore_env_var")
    assert evaluation.decision == "requires_approval"
    assert evaluation.risk == "medium"


def test_unknown_action_is_always_blocked():
    db = FakeFirestoreClient()
    evaluation = evaluate_policy(db, "demo-service", "delete_database")
    assert evaluation.decision == "blocked"
    assert evaluation.risk is None


def test_observe_only_mode_never_executes():
    db = FakeFirestoreClient()
    set_autonomy_mode(db, "observe_only", "test-user")
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "recommend_only"


def test_recommend_only_mode_never_executes_even_medium_risk():
    db = FakeFirestoreClient()
    set_autonomy_mode(db, "recommend_only", "test-user")
    evaluation = evaluate_policy(db, "demo-service", "restore_env_var")
    assert evaluation.decision == "recommend_only"


def test_approval_required_mode_forces_approval_even_for_low_risk():
    db = FakeFirestoreClient()
    set_autonomy_mode(db, "approval_required", "test-user")
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "requires_approval"
    assert evaluation.risk == "low"


def test_kill_switch_forces_approval_even_for_low_risk():
    db = FakeFirestoreClient()
    set_kill_switch(db, True, "test-user")
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "requires_approval"
    assert "kill switch" in evaluation.reason.lower()


def test_kill_switch_does_not_block_recommend_only_mode():
    """The kill switch specifically stops AUTOMATIC execution; observe/
    recommend modes already never execute, so the reason should reflect
    the mode, not the kill switch (both would produce the same safe
    outcome, but the audit trail should say why)."""
    db = FakeFirestoreClient()
    set_autonomy_mode(db, "observe_only", "test-user")
    set_kill_switch(db, True, "test-user")
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "recommend_only"


def test_service_profile_can_escalate_risk_for_a_critical_action():
    db = FakeFirestoreClient()
    upsert_service_profile(
        db,
        ServiceProfile(
            service_id="payment-api",
            criticality="critical",
            environment="production",
            action_risk_overrides={"restart_service": "low"},
        ),
    )
    # retry_service is LOW by default, but payment-api is CRITICAL in prod —
    # policy escalates any LOW-risk action to MEDIUM for this service.
    evaluation = evaluate_policy(db, "payment-api", "retry_service")
    assert evaluation.decision == "requires_approval"
    assert evaluation.risk == "medium"


def test_service_profile_leaves_low_criticality_service_alone():
    db = FakeFirestoreClient()
    upsert_service_profile(
        db, ServiceProfile(service_id="notification-worker", criticality="low", environment="production")
    )
    evaluation = evaluate_policy(db, "notification-worker", "retry_service")
    assert evaluation.decision == "auto_execute"
    assert evaluation.risk == "low"


def test_service_profile_can_force_approval_for_a_specific_action():
    db = FakeFirestoreClient()
    upsert_service_profile(
        db, ServiceProfile(service_id="demo-service", actions_requiring_approval=["retry_service"])
    )
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "requires_approval"


def test_service_profile_can_restrict_allowed_automatic_actions():
    db = FakeFirestoreClient()
    upsert_service_profile(
        db, ServiceProfile(service_id="demo-service", allowed_automatic_actions=["gather_logs"])
    )
    # retry_service is LOW risk but not in the allowed-automatic list for
    # this service, so it must fall back to requiring approval.
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "requires_approval"


def test_rate_limit_blocks_after_max_executions_in_window():
    db = FakeFirestoreClient()
    for _ in range(2):
        r = new_remediation(db, "inc-1", "retry_service", risk="low", status="proposed", reason="x", service_id="demo-service")
        from app.incidents_store import update_remediation

        update_remediation(db, r.id, status="verified")

    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "blocked"
    assert "rate limit" in evaluation.reason.lower()


def test_rate_limit_does_not_affect_a_different_action():
    db = FakeFirestoreClient()
    for _ in range(2):
        r = new_remediation(db, "inc-1", "retry_service", risk="low", status="proposed", reason="x", service_id="demo-service")
        from app.incidents_store import update_remediation

        update_remediation(db, r.id, status="verified")

    evaluation = evaluate_policy(db, "demo-service", "rerun_health_check")
    assert evaluation.decision == "auto_execute"


def test_rate_limit_windows_on_executed_at_not_created_at():
    """A remediation proposed long ago (e.g. it sat waiting for approval)
    but executed just now must still count toward the rate limit — and one
    proposed just now but never actually executed must not."""
    from datetime import datetime, timedelta, timezone

    from app.incidents_store import update_remediation

    db = FakeFirestoreClient()
    old_created = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

    r1 = new_remediation(db, "inc-1", "retry_service", risk="low", status="proposed", reason="x", service_id="demo-service")
    update_remediation(db, r1.id, status="verified", created_at=old_created, executed_at=datetime.now(timezone.utc).isoformat())

    r2 = new_remediation(db, "inc-2", "retry_service", risk="low", status="proposed", reason="x", service_id="demo-service")
    update_remediation(db, r2.id, status="verified", created_at=old_created, executed_at=datetime.now(timezone.utc).isoformat())

    # Both executed within the window (just now), even though created 30
    # minutes ago -> rate limit should trigger.
    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "blocked"
    assert "rate limit" in evaluation.reason.lower()


def test_rate_limit_ignores_a_proposal_that_was_never_executed():
    from app.incidents_store import update_remediation

    db = FakeFirestoreClient()
    for _ in range(3):
        r = new_remediation(db, "inc-1", "retry_service", risk="low", status="proposed", reason="x", service_id="demo-service")
        update_remediation(db, r.id, status="awaiting_approval")  # never actually applied

    evaluation = evaluate_policy(db, "demo-service", "retry_service")
    assert evaluation.decision == "auto_execute"
