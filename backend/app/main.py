import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import orchestrator
from app.agent.activity_log import list_events
from app.agent.postmortem import generate_postmortem
from app.agent.tools import check_service_health
from app.analytics import compute_analytics, compute_overview, compute_safety_stats
from app.config import settings
from app.firestore_client import get_firestore_client
from app.incidents_store import (
    get_active_incident_for_service,
    get_incident,
    list_incidents,
    list_remediations_for_incident,
    new_incident,
    update_incident,
)
from app.models import ServiceProfile
from app.settings_store import (
    get_global_settings,
    get_service_profile,
    list_service_profiles,
    set_autonomy_mode,
    set_kill_switch,
    upsert_service_profile,
)

app = FastAPI(title="Autonomous Incident Resolver Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/demo/trigger")
def demo_trigger(payload: dict):
    scenario = payload.get("scenario")
    try:
        resp = httpx.post(
            f"{settings.demo_service_url}/admin/incidents/trigger", json={"scenario": scenario}, timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not reach demo service: {exc}") from exc


@app.post("/demo/reset")
def demo_reset():
    try:
        resp = httpx.post(f"{settings.demo_service_url}/admin/incidents/reset", timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not reach demo service: {exc}") from exc


def _incident_response(db, incident_id: str) -> dict:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(404, "Incident not found.")
    remediations = list_remediations_for_incident(db, incident_id)
    events = list_events(db, incident_id)
    return {
        "incident": incident.model_dump(),
        "remediations": [r.model_dump() for r in remediations],
        "events": events,
    }


@app.post("/incidents")
async def start_incident(payload: dict | None = None):
    service_id = (payload or {}).get("service_id") or settings.demo_service_id
    db = get_firestore_client()

    existing = get_active_incident_for_service(db, service_id)
    if existing is not None:
        # Don't start a second, competing investigation for the same
        # failure — two concurrent incidents racing to remediate the same
        # service produces false "resolved via X" claims when one incident's
        # fix accidentally satisfies the other's health check too.
        return _incident_response(db, existing.id)

    health_result = check_service_health(service_id)
    if health_result.status == "healthy":
        return {"status": "healthy", "message": "Service is healthy, no incident created."}

    incident = new_incident(db, service_id)
    update_incident(db, incident.id, autonomy_mode=get_global_settings(db).autonomy_mode)
    incident = get_incident(db, incident.id)
    await orchestrator.investigate(db, incident)
    return _incident_response(db, incident.id)


@app.get("/settings")
def get_settings():
    db = get_firestore_client()
    return get_global_settings(db).model_dump()


@app.put("/settings/autonomy-mode")
def put_autonomy_mode(payload: dict):
    mode = payload.get("mode")
    changed_by = payload.get("changed_by", "dashboard user")
    if mode not in ("observe_only", "recommend_only", "approval_required", "autonomous_low_risk"):
        raise HTTPException(400, f"Unknown autonomy mode: {mode}")
    db = get_firestore_client()
    return set_autonomy_mode(db, mode, changed_by).model_dump()


@app.put("/settings/kill-switch")
def put_kill_switch(payload: dict):
    enabled = payload.get("enabled")
    changed_by = payload.get("changed_by", "dashboard user")
    if not isinstance(enabled, bool):
        raise HTTPException(400, "'enabled' must be a boolean.")
    db = get_firestore_client()
    return set_kill_switch(db, enabled, changed_by).model_dump()


@app.get("/services")
def get_services():
    db = get_firestore_client()
    return {"services": [p.model_dump() for p in list_service_profiles(db)]}


@app.get("/services/{service_id}")
def get_service(service_id: str):
    db = get_firestore_client()
    profile = get_service_profile(db, service_id)
    if profile is None:
        return ServiceProfile(service_id=service_id).model_dump()
    return profile.model_dump()


@app.put("/services/{service_id}")
def put_service(service_id: str, payload: dict):
    payload["service_id"] = service_id
    try:
        profile = ServiceProfile(**payload)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    db = get_firestore_client()
    return upsert_service_profile(db, profile).model_dump()


@app.get("/incidents")
def get_incidents(service_id: str | None = None, status: str | None = None):
    db = get_firestore_client()
    return {"incidents": [i.model_dump() for i in list_incidents(db, service_id=service_id, status=status)]}


@app.get("/overview")
def get_overview():
    db = get_firestore_client()
    return compute_overview(db)


@app.get("/analytics")
def get_analytics():
    db = get_firestore_client()
    return compute_analytics(db)


@app.get("/safety/stats")
def get_safety_stats():
    db = get_firestore_client()
    return compute_safety_stats(db)


@app.get("/incidents/{incident_id}/postmortem")
async def get_postmortem(incident_id: str):
    db = get_firestore_client()
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(404, "Incident not found.")
    if incident.status != "resolved":
        raise HTTPException(400, "Postmortems are only available for resolved incidents.")
    events = list_events(db, incident_id)
    return await generate_postmortem(db, incident, events)


@app.get("/postmortems")
def list_postmortems():
    db = get_firestore_client()
    snaps = db.collection("postmortems").stream()
    return {"postmortems": [snap.to_dict() for snap in snaps]}


@app.get("/incidents/{incident_id}")
def get_incident_detail(incident_id: str):
    db = get_firestore_client()
    return _incident_response(db, incident_id)


@app.get("/incidents/{incident_id}/events")
def get_incident_events(incident_id: str):
    db = get_firestore_client()
    return {"events": list_events(db, incident_id)}


@app.post("/incidents/{incident_id}/remediations/{remediation_id}/approve")
async def approve(incident_id: str, remediation_id: str, payload: dict | None = None):
    approved_by = (payload or {}).get("approved_by", "dashboard user")
    db = get_firestore_client()
    try:
        await orchestrator.approve_remediation(db, incident_id, remediation_id, approved_by=approved_by)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _incident_response(db, incident_id)


@app.post("/incidents/{incident_id}/remediations/{remediation_id}/reject")
async def reject(incident_id: str, remediation_id: str, payload: dict | None = None):
    rejected_by = (payload or {}).get("rejected_by", "dashboard user")
    db = get_firestore_client()
    try:
        await orchestrator.reject_remediation(db, incident_id, remediation_id, rejected_by=rejected_by)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _incident_response(db, incident_id)
