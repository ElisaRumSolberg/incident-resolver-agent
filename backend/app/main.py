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
    get_incident,
    list_incidents,
    list_remediations_for_incident,
    new_incident,
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

    health_result = check_service_health(service_id)
    if health_result.status == "healthy":
        return {"status": "healthy", "message": "Service is healthy, no incident created."}

    incident = new_incident(db, service_id)
    await orchestrator.investigate(db, incident)
    return _incident_response(db, incident.id)


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
async def approve(incident_id: str, remediation_id: str):
    db = get_firestore_client()
    try:
        await orchestrator.approve_remediation(db, incident_id, remediation_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _incident_response(db, incident_id)


@app.post("/incidents/{incident_id}/remediations/{remediation_id}/reject")
async def reject(incident_id: str, remediation_id: str):
    db = get_firestore_client()
    try:
        await orchestrator.reject_remediation(db, incident_id, remediation_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _incident_response(db, incident_id)
