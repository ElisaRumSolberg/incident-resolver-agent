"""Tests for the demo target service — this is what judges interact with
live, so its determinism/reproducibility matters as much as the agent's own
logic. Module-level in-memory state is reset before every test via the
service's own reset endpoint, matching how it's actually used in production.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

SCENARIOS = ["missing_env_var", "broken_dependency", "bad_deployment", "credential_exposure"]


@pytest.fixture
def client():
    c = TestClient(app)
    c.post("/admin/incidents/reset")
    return c


def test_starts_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_each_scenario_makes_the_service_unhealthy(client, scenario):
    client.post("/admin/incidents/trigger", json={"scenario": scenario})
    resp = client.get("/health")
    assert resp.json()["status"] == "unhealthy"


def test_cannot_trigger_a_second_incident_while_one_is_active(client):
    r1 = client.post("/admin/incidents/trigger", json={"scenario": "missing_env_var"})
    assert r1.status_code == 200

    r2 = client.post("/admin/incidents/trigger", json={"scenario": "bad_deployment"})
    assert r2.status_code == 400
    # Confirms the ORIGINAL scenario is still the active one, not silently
    # overwritten by the second trigger.
    assert client.get("/health").json()["status"] == "unhealthy"
    config = client.get("/config").json()
    assert config["database_url_set"] is False  # missing_env_var still active
    assert config["startup_ok"] is True  # bad_deployment never actually applied


def test_trigger_with_invalid_scenario_name_is_rejected(client):
    resp = client.post("/admin/incidents/trigger", json={"scenario": "totally_made_up_scenario"})
    assert resp.status_code == 422  # pydantic Literal validation, not a crash
    assert client.get("/health").json()["status"] == "healthy"  # state untouched


def test_resolve_with_the_wrong_action_has_no_effect(client):
    """The exact bug class the orchestrator's no_effect handling exists
    for — confirm the demo-service really does report no_effect rather
    than silently 'fixing' the wrong scenario."""
    client.post("/admin/incidents/trigger", json={"scenario": "missing_env_var"})
    resp = client.post("/admin/incidents/resolve", json={"action": "rollback_revision"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_effect"
    assert client.get("/health").json()["status"] == "unhealthy"  # still broken


def test_resolve_with_the_correct_action_recovers(client):
    client.post("/admin/incidents/trigger", json={"scenario": "missing_env_var"})
    resp = client.post("/admin/incidents/resolve", json={"action": "restore_env_var"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
    assert client.get("/health").json()["status"] == "healthy"


def test_resolve_with_no_active_incident_is_a_clean_400_not_a_crash(client):
    resp = client.post("/admin/incidents/resolve", json={"action": "restore_env_var"})
    assert resp.status_code == 400


def test_resolve_twice_in_a_row_is_a_clean_400_the_second_time(client):
    client.post("/admin/incidents/trigger", json={"scenario": "missing_env_var"})
    r1 = client.post("/admin/incidents/resolve", json={"action": "restore_env_var"})
    assert r1.json()["status"] == "resolved"

    r2 = client.post("/admin/incidents/resolve", json={"action": "restore_env_var"})
    assert r2.status_code == 400  # nothing left to resolve — not silently "resolved" again


def test_bad_deployment_scenario_changes_and_restores_the_revision(client):
    baseline_revision = client.get("/health").json()["revision"]
    client.post("/admin/incidents/trigger", json={"scenario": "bad_deployment"})
    assert client.get("/health").json()["revision"] != baseline_revision

    client.post("/admin/incidents/resolve", json={"action": "rollback_revision"})
    assert client.get("/health").json()["revision"] == baseline_revision


def test_credential_exposure_reflects_in_config(client):
    client.post("/admin/incidents/trigger", json={"scenario": "credential_exposure"})
    assert client.get("/config").json()["credentials_exposed"] is True
    client.post("/admin/incidents/resolve", json={"action": "rotate_credentials"})
    assert client.get("/config").json()["credentials_exposed"] is False


def test_logs_contain_the_triggered_scenarios_error_message(client):
    client.post("/admin/incidents/trigger", json={"scenario": "broken_dependency"})
    logs = client.get("/logs").json()["logs"]
    assert any("payments-api" in entry["message"] for entry in logs)


def test_logs_endpoint_respects_limit_param(client):
    for _ in range(5):
        client.post("/admin/incidents/reset")
    logs = client.get("/logs", params={"limit": 2}).json()["logs"]
    assert len(logs) <= 2


def test_reset_is_idempotent_and_always_returns_to_healthy(client):
    client.post("/admin/incidents/trigger", json={"scenario": "bad_deployment"})
    client.post("/admin/incidents/reset")
    client.post("/admin/incidents/reset")  # calling reset twice must not error
    resp = client.get("/health")
    assert resp.json()["status"] == "healthy"
    assert resp.json()["revision"] == "00041"


def test_trigger_with_missing_scenario_field_is_a_clean_422(client):
    resp = client.post("/admin/incidents/trigger", json={})
    assert resp.status_code == 422


def test_trigger_with_malformed_json_is_a_clean_4xx_not_500(client):
    resp = client.post(
        "/admin/incidents/trigger", headers={"Content-Type": "application/json"}, content=b"{bad json"
    )
    assert 400 <= resp.status_code < 500
