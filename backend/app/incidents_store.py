"""Firestore persistence for incidents and remediations."""

import uuid
from datetime import datetime, timezone

from google.cloud import firestore

from app.models import Incident, RemediationRecord


def new_incident(db: firestore.Client, service_id: str) -> Incident:
    incident = Incident(
        id=str(uuid.uuid4()),
        service_id=service_id,
        status="investigating",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    db.collection("incidents").document(incident.id).set(incident.model_dump())
    return incident


def get_incident(db: firestore.Client, incident_id: str) -> Incident | None:
    snap = db.collection("incidents").document(incident_id).get()
    if not snap.exists:
        return None
    return Incident(**snap.to_dict())


def update_incident(db: firestore.Client, incident_id: str, **fields) -> None:
    db.collection("incidents").document(incident_id).update(fields)


ACTIVE_STATUSES = {"investigating", "awaiting_approval", "remediating", "verifying"}


def get_active_incident_for_service(db: firestore.Client, service_id: str) -> Incident | None:
    """Finds an incident already in progress for this service, if any.

    Prevents two concurrent requests (two tabs, a double-fired trigger, a
    script hitting the API directly) from creating duplicate incidents that
    both race to remediate the same underlying failure.
    """
    snaps = (
        db.collection("incidents")
        .order_by("started_at", direction=firestore.Query.DESCENDING)
        .limit(50)
        .stream()
    )
    for snap in snaps:
        data = snap.to_dict()
        if data.get("service_id") == service_id and data.get("status") in ACTIVE_STATUSES:
            return Incident(**data)
    return None


def list_incidents(
    db: firestore.Client,
    limit: int = 50,
    service_id: str | None = None,
    status: str | None = None,
) -> list[Incident]:
    # Filtered in Python rather than with Firestore .where() + .order_by() on a
    # different field, which would require a manual composite index — not
    # worth it at this data volume.
    snaps = (
        db.collection("incidents")
        .order_by("started_at", direction=firestore.Query.DESCENDING)
        .limit(200)
        .stream()
    )
    incidents = [Incident(**snap.to_dict()) for snap in snaps]
    if service_id:
        incidents = [i for i in incidents if i.service_id == service_id]
    if status:
        incidents = [i for i in incidents if i.status == status]
    return incidents[:limit]


def new_remediation(
    db: firestore.Client, incident_id: str, action: str, risk: str, status: str, reason: str | None
) -> RemediationRecord:
    record = RemediationRecord(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        action=action,
        risk=risk,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        reason=reason,
    )
    db.collection("remediations").document(record.id).set(record.model_dump())
    return record


def get_remediation(db: firestore.Client, remediation_id: str) -> RemediationRecord | None:
    snap = db.collection("remediations").document(remediation_id).get()
    if not snap.exists:
        return None
    return RemediationRecord(**snap.to_dict())


def update_remediation(db: firestore.Client, remediation_id: str, **fields) -> None:
    db.collection("remediations").document(remediation_id).update(fields)


def list_remediations_for_incident(db: firestore.Client, incident_id: str) -> list[RemediationRecord]:
    snaps = db.collection("remediations").where("incident_id", "==", incident_id).stream()
    records = [RemediationRecord(**snap.to_dict()) for snap in snaps]
    return records
