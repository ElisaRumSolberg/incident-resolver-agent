"""Adversarial follow-up pass: targets specific failure modes not covered by
the existing suite — concurrency, idempotent incident creation, real
authorization enforcement through the HTTP layer, kill-switch timing
semantics, verification-call exceptions, malformed non-string Gemini
output, and Firestore write failures mid-sequence.

This file does not assume the code is broken — several tests here are
written to find out, not to confirm a hypothesis. Where a test exposes a
real unhandled crash, that's called out explicitly in the test name/docstring
and cross-referenced in the review report; production code is only changed
where a test proves an actual defect.
"""

import threading
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app import auth, main, orchestrator
from app.agent import tools
from app.config import settings
from app.incidents_store import new_incident, new_remediation
from app.models import HealthResult, RemediationProposal
from tests.fake_firestore import FakeFirestoreClient


def _proposal(action: str) -> RemediationProposal:
    return RemediationProposal(root_cause="x", confidence=0.9, severity="high", action=action, reason="y")


# ---------------------------------------------------------------------------
# Concurrency (real OS threads, not asyncio.gather — see report for why
# asyncio.gather can't expose anything here: our Firestore calls are
# synchronous/blocking, so a single-threaded event loop never actually
# interleaves between them)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_truly_concurrent_approve_calls_do_not_double_execute(monkeypatch):
    """Runs two approve_remediation calls for the SAME remediation on
    separate OS threads (each with its own event loop) against one shared
    FakeFirestoreClient with no locking, to see whether Python's GIL
    switching between bytecode instructions can interleave the
    check-then-act sequence (get_remediation -> check status -> update)."""
    import asyncio

    db = FakeFirestoreClient()
    applied = []
    apply_lock_events = []

    def fake_apply(service_id, action):
        # Simulate a slow external call so both threads are likely to be
        # inside the critical section at the same time.
        import time

        apply_lock_events.append("enter")
        time.sleep(0.05)
        applied.append(action)
        return None

    monkeypatch.setattr(orchestrator, "apply_safe_remediation", fake_apply)
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: HealthResult(status="healthy", checks={}, timestamp="t"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    incident = new_incident(db, "demo-service")
    remediation = new_remediation(
        db, incident.id, "restore_env_var", risk="medium", status="awaiting_approval", reason="x", service_id="demo-service"
    )

    results = []
    errors = []

    def worker():
        try:
            result = asyncio.run(
                orchestrator.approve_remediation(db, incident.id, remediation.id, approved_by="racer")
            )
            results.append(result)
        except ValueError as exc:
            errors.append(exc)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    # The real safety property under test: no matter how the threads
    # interleaved, the target service must never have been hit twice for
    # the same approval.
    assert applied.count("restore_env_var") == 1, f"double-executed! applied={applied}"
    # Exactly one of the two callers should have been rejected (or, if the
    # GIL happened not to interleave this run, both could technically have
    # been serialized without ever racing — but exactly one execution must
    # have occurred either way).
    assert len(results) + len(errors) == 2


# ---------------------------------------------------------------------------
# Idempotent incident creation via the real API
# ---------------------------------------------------------------------------


@pytest.fixture
def db(monkeypatch):
    fake_db = FakeFirestoreClient()
    monkeypatch.setattr(main, "get_firestore_client", lambda: fake_db)
    return fake_db


@pytest.fixture
def client():
    return TestClient(main.app)


def test_double_post_incidents_for_the_same_service_reuses_the_active_one(client, db, monkeypatch):
    monkeypatch.setattr(main, "check_service_health", lambda service_id: HealthResult(status="unhealthy", checks={}, timestamp="t"))

    async def fake_diagnose(service_id, attempted_actions):
        return _proposal("restore_env_var"), []

    monkeypatch.setattr(orchestrator, "run_diagnosis", fake_diagnose)
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    r1 = client.post("/incidents", json={"service_id": "demo-service"})
    r2 = client.post("/incidents", json={"service_id": "demo-service"})

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["incident"]["id"] == r2.json()["incident"]["id"]

    all_incidents = client.get("/incidents", params={"service_id": "demo-service"}).json()["incidents"]
    active = [i for i in all_incidents if i["status"] not in ("resolved", "recommended")]
    assert len(active) == 1, f"expected exactly one active incident, got {len(active)}"


# ---------------------------------------------------------------------------
# Authorization enforced through the real HTTP layer, not just resolve_actor()
# ---------------------------------------------------------------------------


def test_demo_mode_false_rejects_approve_with_no_authorization_header(client, db, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    incident = new_incident(db, "demo-service")
    remediation = new_remediation(
        db, incident.id, "restore_env_var", risk="medium", status="awaiting_approval", reason="x", service_id="demo-service"
    )
    resp = client.post(f"/incidents/{incident.id}/remediations/{remediation.id}/approve", json={"approved_by": "attacker"})
    assert resp.status_code == 401
    # And the remediation must genuinely still be untouched.
    still = client.get(f"/incidents/{incident.id}").json()["remediations"][0]
    assert still["status"] == "awaiting_approval"


def test_demo_mode_false_rejects_kill_switch_change_with_no_authorization(client, db, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    resp = client.put("/settings/kill-switch", json={"enabled": True, "changed_by": "attacker"})
    assert resp.status_code == 401
    assert client.get("/settings").json()["kill_switch_enabled"] is False


def test_demo_mode_false_rejects_an_unverifiable_bearer_token(client, db, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    resp = client.put(
        "/settings/autonomy-mode",
        json={"mode": "observe_only", "changed_by": "attacker"},
        headers={"Authorization": "Bearer totally-forged-token"},
    )
    assert resp.status_code == 401


def test_demo_mode_false_accepts_a_verified_token_and_uses_its_identity(client, db, monkeypatch):
    from unittest.mock import patch

    monkeypatch.setattr(settings, "demo_mode", False)
    with patch("firebase_admin.auth.verify_id_token", return_value={"name": "Real User", "uid": "u1"}):
        resp = client.put(
            "/settings/autonomy-mode",
            json={"mode": "observe_only", "changed_by": "Impersonated Admin"},
            headers={"Authorization": "Bearer a-real-token"},
        )
    assert resp.status_code == 200
    assert resp.json()["autonomy_mode_changed_by"] == "Real User"  # not "Impersonated Admin"


# ---------------------------------------------------------------------------
# Kill-switch timing semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kill_switch_is_a_point_in_time_check_not_a_running_guard(monkeypatch):
    """Documents actual behavior: the kill switch is consulted once, when
    the policy decision is made. If it's flipped ON *after* auto_execute was
    already decided, the in-flight apply is not aborted. This is
    intentional (the switch stops future automatic decisions, it isn't a
    kill-the-in-flight-request mechanism) — this test exists so that
    behavior is explicit and regression-checked, not implicit."""
    from app.settings_store import set_kill_switch

    db = FakeFirestoreClient()
    applied = []

    def fake_apply(service_id, action):
        # Flip the kill switch ON *during* the apply call, simulating a
        # human hitting the switch while this execution is already running.
        set_kill_switch(db, True, "human-mid-flight")
        applied.append(action)
        return None

    monkeypatch.setattr(orchestrator, "apply_safe_remediation", fake_apply)
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: HealthResult(status="healthy", checks={}, timestamp="t"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    async def diagnose(service_id, attempted_actions):
        return _proposal("retry_service"), []  # LOW risk -> auto_execute

    monkeypatch.setattr(orchestrator, "run_diagnosis", diagnose)

    incident = new_incident(db, "demo-service")
    result_incident, remediation = await orchestrator.investigate(db, incident)

    assert applied == ["retry_service"]  # already-decided execution completed
    assert remediation.status == "verified"
    assert result_incident.status == "resolved"

    # But the kill switch IS now in effect for the NEXT decision.
    from app.agent.policy import evaluate_policy

    next_evaluation = evaluate_policy(db, "demo-service", "rerun_health_check")
    assert next_evaluation.decision == "requires_approval"


# ---------------------------------------------------------------------------
# Verification call raising an exception (not just returning unhealthy)
# ---------------------------------------------------------------------------


def test_check_service_health_survives_a_malformed_json_response(monkeypatch):
    """The demo-service returning JSON that doesn't match HealthResult's
    schema (missing fields, wrong types) raises a pydantic ValidationError,
    NOT an httpx.HTTPError — confirms whether the existing
    `except httpx.HTTPError` in check_service_health actually catches this
    or lets it propagate."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": "shape", "no_status_field": True}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse())

    # This is the crux of the test: does it crash, or degrade gracefully?
    try:
        result = tools.check_service_health("demo-service")
    except Exception as exc:  # noqa: BLE001 — deliberately broad, we're finding out what's raised
        pytest.fail(
            f"check_service_health raised {type(exc).__name__}: {exc} instead of degrading gracefully "
            f"— a malformed health response can crash the request."
        )
    assert result.status == "unhealthy"


@pytest.mark.asyncio
async def test_verify_recovery_exception_during_apply_and_verify_does_not_crash_the_request(monkeypatch):
    """orchestrator._apply_and_verify calls verify_recovery with no
    try/except around it (unlike apply_safe_remediation, which is wrapped).
    If verify_recovery raises for any reason, does the whole request crash
    uncaught, or is it handled?"""
    db = FakeFirestoreClient()
    monkeypatch.setattr(orchestrator, "apply_safe_remediation", lambda service_id, action: None)
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    def raising_verify(service_id):
        raise RuntimeError("simulated verification transport failure")

    monkeypatch.setattr(orchestrator, "verify_recovery", raising_verify)

    async def diagnose(service_id, attempted_actions):
        return _proposal("retry_service"), []

    monkeypatch.setattr(orchestrator, "run_diagnosis", diagnose)

    incident = new_incident(db, "demo-service")
    try:
        await orchestrator.investigate(db, incident)
    except RuntimeError:
        pytest.fail(
            "verify_recovery raising crashed orchestrator.investigate() uncaught — "
            "a transient verification failure (timeout, malformed response, etc.) can 500 the request."
        )


# ---------------------------------------------------------------------------
# Malformed Gemini output: non-string / wrong-type `action`
# ---------------------------------------------------------------------------


def test_propose_remediation_with_non_string_action_is_rejected_gracefully():
    from app.agent.adk_agent import _build_tools, _PipelineState

    state = _PipelineState()
    tools_ = _build_tools("demo-service", [], state)
    propose = next(t for t in tools_ if t.func.__name__ == "propose_remediation_tool")

    result = propose.func(root_cause="x", confidence=0.9, severity="high", action=None, reason="y")
    assert "error" in result
    assert state.proposal is None


def test_propose_remediation_with_integer_action_is_rejected_gracefully():
    from app.agent.adk_agent import _build_tools, _PipelineState

    state = _PipelineState()
    tools_ = _build_tools("demo-service", [], state)
    propose = next(t for t in tools_ if t.func.__name__ == "propose_remediation_tool")

    result = propose.func(root_cause="x", confidence=0.9, severity="high", action=12345, reason="y")
    assert "error" in result
    assert state.proposal is None


# ---------------------------------------------------------------------------
# Firestore write failures mid-sequence
# ---------------------------------------------------------------------------


class _FlakyDocRef:
    """Wraps a real FakeDocRef, raising on the Nth call to .update()."""

    def __init__(self, real_ref, counter: dict, fail_at: int):
        self._real = real_ref
        self._counter = counter
        self._fail_at = fail_at

    def update(self, fields):
        self._counter["n"] += 1
        if self._counter["n"] == self._fail_at:
            raise Exception("simulated Firestore write failure")
        return self._real.update(fields)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _FlakyCollection:
    def __init__(self, real_collection, counter: dict, fail_at: int):
        self._real = real_collection
        self._counter = counter
        self._fail_at = fail_at

    def document(self, doc_id):
        return _FlakyDocRef(self._real.document(doc_id), self._counter, self._fail_at)

    def __getattr__(self, name):
        return getattr(self._real, name)


class FlakyFirestoreClient:
    """A FakeFirestoreClient where the Nth .update() call across ALL
    documents/collections raises, simulating a Firestore write failure
    partway through a multi-write sequence (diagnosis -> proposal ->
    safety eval -> apply -> verify each write separately)."""

    def __init__(self, fail_at: int):
        self._real = FakeFirestoreClient()
        self._counter = {"n": 0}
        self._fail_at = fail_at

    def collection(self, name):
        return _FlakyCollection(self._real.collection(name), self._counter, self._fail_at)


@pytest.mark.asyncio
@pytest.mark.parametrize("fail_at", [1, 2, 3, 4, 5])
async def test_firestore_write_failure_partway_through_investigate_does_not_corrupt_silently(monkeypatch, fail_at):
    """Whatever write in the sequence fails, the request must fail loudly
    (a raised exception) rather than silently continuing with an
    inconsistent incident/remediation/event state. This test doesn't assert
    graceful recovery (that would be a feature, not a bug fix) — it asserts
    the system doesn't pretend to succeed when a write actually failed."""
    db = FlakyFirestoreClient(fail_at=fail_at)
    monkeypatch.setattr(orchestrator, "apply_safe_remediation", lambda service_id, action: None)
    monkeypatch.setattr(orchestrator, "verify_recovery", lambda service_id: HealthResult(status="healthy", checks={}, timestamp="t"))
    monkeypatch.setattr(orchestrator, "find_similar_incidents", lambda *a, **k: [])

    async def diagnose(service_id, attempted_actions):
        return _proposal("retry_service"), []

    monkeypatch.setattr(orchestrator, "run_diagnosis", diagnose)

    incident = new_incident(db, "demo-service")
    with pytest.raises(Exception):
        await orchestrator.investigate(db, incident)
    # The key safety property: a failed write must not be silently treated
    # as success. We don't assert a specific status here (any status short
    # of a fabricated "resolved" is acceptable) — just that it never claims
    # success when a write genuinely failed.
