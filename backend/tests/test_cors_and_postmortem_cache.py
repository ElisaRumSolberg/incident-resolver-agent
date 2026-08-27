"""Two more adversarial checks:

1. CORS is actually enforced by the deployed allow-list, not just configured
   and hoped for — a request claiming an origin outside allow_origins must
   not get an Access-Control-Allow-Origin header back.
2. A cached postmortem is truly immutable — if it were regenerated from an
   incident whose fields changed after resolution (e.g. a race with another
   write), the cached record must win rather than silently drifting or
   making a second Gemini call.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import main
from app.agent.postmortem import generate_postmortem
from app.models import Incident
from tests.fake_firestore import FakeFirestoreClient


@pytest.fixture
def db(monkeypatch):
    fake_db = FakeFirestoreClient()
    monkeypatch.setattr(main, "get_firestore_client", lambda: fake_db)
    return fake_db


@pytest.fixture
def client():
    return TestClient(main.app)


def test_disallowed_origin_gets_no_cors_header(client, db):
    resp = client.get(
        "/health",
        headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers.keys()}


def test_allowed_origin_gets_cors_header(client, db):
    from app.config import settings

    allowed = settings.allowed_origins_list[0]
    resp = client.get("/health", headers={"Origin": allowed})
    assert resp.headers.get("access-control-allow-origin") == allowed


@pytest.mark.asyncio
async def test_cached_postmortem_is_never_regenerated_or_overwritten():
    db = FakeFirestoreClient()
    incident = Incident(
        id="inc-1",
        service_id="payment-api",
        status="resolved",
        started_at="2026-01-01T00:00:00+00:00",
        resolved_at="2026-01-01T00:05:00+00:00",
        root_cause="original root cause",
    )

    db.collection("postmortems").document("inc-1").set(
        {
            "incident_id": "inc-1",
            "service_id": "payment-api",
            "summary": "already generated, cached forever",
            "recovery_seconds": 300,
            "root_cause": "original root cause",
        }
    )

    with patch("app.agent.postmortem._gemini_client") as fake_client:
        result = await generate_postmortem(db, incident, events=[])

    fake_client.assert_not_called()
    assert result["summary"] == "already generated, cached forever"


@pytest.mark.asyncio
async def test_postmortem_generation_is_cached_after_first_call():
    db = FakeFirestoreClient()
    incident = Incident(
        id="inc-2",
        service_id="payment-api",
        status="resolved",
        started_at="2026-01-01T00:00:00+00:00",
        resolved_at="2026-01-01T00:05:00+00:00",
        root_cause="missing env var",
    )

    fake_response = AsyncMock()
    fake_response.return_value.text = "First generated summary."
    with patch("app.agent.postmortem._gemini_client") as fake_client:
        fake_client.return_value.aio.models.generate_content = fake_response
        first = await generate_postmortem(db, incident, events=[])
        second = await generate_postmortem(db, incident, events=[])

    assert first["summary"] == "First generated summary."
    assert second["summary"] == "First generated summary."
    fake_response.assert_called_once()
