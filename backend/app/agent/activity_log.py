from datetime import datetime, timezone


def log_event(db, incident_id: str, event_type: str, message: str, actor: str = "agent") -> None:
    """Append one entry to the incident's activity timeline. Best-effort:
    Firestore writes are reliable enough here that callers don't need to
    wrap this in try/except."""
    db.collection("incidents").document(incident_id).collection("events").add(
        {
            "type": event_type,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
        }
    )


def list_events(db, incident_id: str) -> list[dict]:
    snaps = (
        db.collection("incidents")
        .document(incident_id)
        .collection("events")
        .order_by("created_at")
        .stream()
    )
    return [snap.to_dict() for snap in snaps]
