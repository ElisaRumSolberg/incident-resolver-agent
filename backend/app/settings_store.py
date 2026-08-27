"""Global settings (autonomy mode, kill switch) and per-service risk profiles.

Both are small, low-cardinality documents — a single `settings/global` doc
and one `service_profiles/{service_id}` doc per service — read on nearly
every orchestrator decision, so no querying/indexing concerns here.
"""

from datetime import datetime, timezone

from google.cloud import firestore

from app.models import GlobalSettings, ServiceProfile

_SETTINGS_DOC = ("settings", "global")


def get_global_settings(db: firestore.Client) -> GlobalSettings:
    collection, doc_id = _SETTINGS_DOC
    snap = db.collection(collection).document(doc_id).get()
    if not snap.exists:
        return GlobalSettings()
    return GlobalSettings(**snap.to_dict())


def set_autonomy_mode(db: firestore.Client, mode: str, changed_by: str) -> GlobalSettings:
    current = get_global_settings(db)
    current.autonomy_mode = mode  # type: ignore[assignment]
    current.autonomy_mode_changed_at = datetime.now(timezone.utc).isoformat()
    current.autonomy_mode_changed_by = changed_by
    collection, doc_id = _SETTINGS_DOC
    db.collection(collection).document(doc_id).set(current.model_dump())
    return current


def set_kill_switch(db: firestore.Client, enabled: bool, changed_by: str) -> GlobalSettings:
    current = get_global_settings(db)
    current.kill_switch_enabled = enabled
    current.kill_switch_changed_at = datetime.now(timezone.utc).isoformat()
    current.kill_switch_changed_by = changed_by
    collection, doc_id = _SETTINGS_DOC
    db.collection(collection).document(doc_id).set(current.model_dump())
    return current


def get_service_profile(db: firestore.Client, service_id: str) -> ServiceProfile | None:
    snap = db.collection("service_profiles").document(service_id).get()
    if not snap.exists:
        return None
    return ServiceProfile(**snap.to_dict())


def upsert_service_profile(db: firestore.Client, profile: ServiceProfile) -> ServiceProfile:
    db.collection("service_profiles").document(profile.service_id).set(profile.model_dump())
    return profile


def list_service_profiles(db: firestore.Client) -> list[ServiceProfile]:
    snaps = db.collection("service_profiles").stream()
    return [ServiceProfile(**snap.to_dict()) for snap in snaps]
