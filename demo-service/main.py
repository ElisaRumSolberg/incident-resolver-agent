"""Deterministic-failure demo service.

This is the "production service" the Incident Resolver Agent watches over.
It exposes a health check, a log feed, and a small set of admin endpoints
that simulate three failure scenarios and their fixes. Everything is
in-memory and deterministic so the agent's diagnosis/remediation loop is
reproducible for demos and judging.
"""

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Demo Service (Incident Target)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Scenario = Literal["missing_env_var", "broken_dependency", "bad_deployment"]

SCENARIO_DEFS = {
    "missing_env_var": {
        "log_message": "ERROR: DATABASE_URL environment variable is not set. Cannot connect to primary datastore.",
        "fix_action": "restore_env_var",
        "fix_log": "DATABASE_URL restored. Datastore connection re-established.",
    },
    "broken_dependency": {
        "log_message": "ERROR: Upstream payments-api returned 500 for 12 consecutive requests. Circuit breaker OPEN.",
        "fix_action": "fix_dependency_config",
        "fix_log": "payments-api endpoint URL corrected in config. Circuit breaker CLOSED, upstream healthy.",
    },
    "bad_deployment": {
        "log_message": "ERROR: Revision 00042 crash-looping on startup. Exit code 1: unhandled exception in startup hook.",
        "fix_action": "rollback_revision",
        "fix_log": "Rolled back traffic to previous healthy revision 00041. Startup succeeded.",
    },
}

_state = {
    "incident_mode": None,  # type: Optional[Scenario]
    "revision": "00041",
    "logs": [],  # list[dict]
}


def _log(message: str, level: str = "info") -> None:
    _state["logs"].append(
        {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
    )
    # keep last 200 entries
    _state["logs"] = _state["logs"][-200:]


_log("Service started. All systems nominal.")


class TriggerRequest(BaseModel):
    scenario: Scenario


class ResolveRequest(BaseModel):
    action: str


@app.get("/health")
def health():
    mode = _state["incident_mode"]
    healthy = mode is None
    return {
        "status": "healthy" if healthy else "unhealthy",
        "revision": _state["revision"],
        "checks": {
            "http": "ok" if healthy else "failing",
            "dependencies": "ok" if healthy else "degraded",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/logs")
def logs(limit: int = 50):
    return {"logs": _state["logs"][-limit:]}


@app.get("/config")
def config():
    """Safe, non-secret configuration metadata only."""
    return {
        "revision": _state["revision"],
        "database_url_set": _state["incident_mode"] != "missing_env_var",
        "payments_api_healthy": _state["incident_mode"] != "broken_dependency",
        "startup_ok": _state["incident_mode"] != "bad_deployment",
    }


@app.post("/admin/incidents/trigger")
def trigger_incident(req: TriggerRequest):
    if _state["incident_mode"] is not None:
        raise HTTPException(400, "An incident is already active. Resolve or reset it first.")
    _state["incident_mode"] = req.scenario
    if req.scenario == "bad_deployment":
        _state["revision"] = "00042"
    definition = SCENARIO_DEFS[req.scenario]
    _log(definition["log_message"], level="error")
    _log(f"Health check now failing (scenario={req.scenario}).", level="warn")
    return {"status": "incident_triggered", "scenario": req.scenario}


@app.post("/admin/incidents/resolve")
def resolve_incident(req: ResolveRequest):
    mode = _state["incident_mode"]
    if mode is None:
        raise HTTPException(400, "No active incident to resolve.")
    definition = SCENARIO_DEFS[mode]
    if req.action != definition["fix_action"]:
        _log(
            f"Remediation action '{req.action}' does not match active incident '{mode}'. No effect.",
            level="warn",
        )
        return {"status": "no_effect", "reason": "action_mismatch", "expected_action": definition["fix_action"]}
    _state["incident_mode"] = None
    if mode == "bad_deployment":
        _state["revision"] = "00041"
    _log(definition["fix_log"])
    _log("Health check passing again.", level="info")
    return {"status": "resolved", "scenario": mode}


@app.post("/admin/incidents/reset")
def reset():
    _state["incident_mode"] = None
    _state["revision"] = "00041"
    _state["logs"] = []
    _log("Service reset to healthy baseline.")
    return {"status": "reset"}


@app.get("/")
def root():
    return {"service": "demo-service", "purpose": "incident-resolver-agent target"}
