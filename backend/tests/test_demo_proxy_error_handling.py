"""Regression tests for a real demo-day bug found by manually reproducing
"another judge left the shared demo-service in a triggered state, then this
user clicks a scenario button": /demo/trigger relayed the demo-service's own
400 ("an incident is already active") wrapped as a misleading 502 "Could not
reach demo service" — which reads as a network outage, not the actual
logical conflict, and is exactly the wrong diagnosis to show live.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from tests.fake_firestore import FakeFirestoreClient


@pytest.fixture
def db(monkeypatch):
    fake_db = FakeFirestoreClient()
    monkeypatch.setattr(main, "get_firestore_client", lambda: fake_db)
    return fake_db


@pytest.fixture
def client():
    return TestClient(main.app)


class _FakeResponse:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://demo-service/x")
            raise httpx.HTTPStatusError(
                f"{self.status_code} error", request=request, response=httpx.Response(self.status_code, json=self._body, request=request)
            )


def test_demo_service_logical_conflict_is_relayed_as_its_real_status_not_502(client, db, monkeypatch):
    """The demo-service returning 400 'already active' (a real, reached
    response) must not be reported as 502 'Could not reach' — that's a
    misdiagnosis a presenter would have to debug live."""

    def fake_post(url, json=None, timeout=None):
        return _FakeResponse(400, {"detail": "An incident is already active. Resolve or reset it first."})

    monkeypatch.setattr(httpx, "post", fake_post)

    resp = client.post("/demo/trigger", json={"scenario": "missing_env_var"})

    assert resp.status_code == 400  # relays the demo-service's real status
    assert resp.status_code != 502
    assert "already active" in resp.json()["detail"]


def test_demo_service_genuinely_unreachable_still_reports_502(client, db, monkeypatch):
    """The 502 path must still exist for an actual connectivity failure —
    this isn't about removing the distinction, only about not misapplying
    it to responses that were, in fact, received."""

    def fake_post(url, json=None, timeout=None):
        raise httpx.ConnectError("connection refused", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    resp = client.post("/demo/trigger", json={"scenario": "missing_env_var"})

    assert resp.status_code == 502
    assert "Could not reach" in resp.json()["detail"]


def test_demo_reset_also_relays_real_status_codes(client, db, monkeypatch):
    def fake_post(url, json=None, timeout=None):
        return _FakeResponse(500, {"detail": "unexpected demo-service error"})

    monkeypatch.setattr(httpx, "post", fake_post)

    resp = client.post("/demo/reset")

    assert resp.status_code == 500
    assert resp.status_code != 502
