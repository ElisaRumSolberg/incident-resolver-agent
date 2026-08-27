"""Deterministic incident similarity — no embeddings, no LLM call.

Root causes are short, evidence-grounded sentences, so plain word-overlap
(Jaccard) plus a same-service bonus is a cheap, explainable, reproducible
similarity signal — good enough to power "similar past incident" without
adding a vector store or another model call to the critical path.
"""

import re

from google.cloud import firestore

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "on",
    "for", "with", "and", "or", "this", "that", "it", "its", "as", "by",
    "which", "due", "not", "be", "has", "have",
}
_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text: str) -> set[str]:
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


_TERMINAL_STATUSES = {"resolved", "escalation_required", "failed"}


def _recovery_seconds(data: dict) -> int | None:
    if not data.get("resolved_at") or not data.get("started_at"):
        return None
    try:
        from datetime import datetime

        start = datetime.fromisoformat(data["started_at"])
        end = datetime.fromisoformat(data["resolved_at"])
        return round((end - start).total_seconds())
    except ValueError:
        return None


def find_similar_incidents(
    db: firestore.Client,
    root_cause: str,
    service_id: str,
    exclude_incident_id: str,
    limit: int = 3,
    min_similarity: float = 0.15,
) -> list[dict]:
    """Searches both resolved AND escalated/failed incidents — remembering
    "this was tried before and did NOT work" is as valuable as remembering
    a success, and is what lets the agent (via attempted/rejected_actions)
    and a human reviewing this panel avoid repeating a known-bad fix."""
    current_words = _tokenize(root_cause)
    # Fetched broad and filtered in Python (see list_incidents for why) —
    # a resolved/escalated status alongside an unrelated order/limit would
    # otherwise need a manual composite index at larger data volumes.
    candidates = db.collection("incidents").limit(300).stream()

    scored = []
    for snap in candidates:
        data = snap.to_dict()
        if data.get("id") == exclude_incident_id or not data.get("root_cause"):
            continue
        if data.get("status") not in _TERMINAL_STATUSES:
            continue
        past_words = _tokenize(data["root_cause"])
        text_score = _jaccard(current_words, past_words)
        service_bonus = 0.25 if data.get("service_id") == service_id else 0.0
        similarity = min(text_score * 0.75 + service_bonus, 0.99)
        if similarity < min_similarity:
            continue
        attempted = data.get("attempted_actions") or []
        result = "successful" if data.get("status") == "resolved" else "failed"
        scored.append(
            {
                "incident_id": data["id"],
                "service_id": data.get("service_id"),
                "root_cause": data.get("root_cause"),
                "action": attempted[-1] if attempted else None,
                "result": result,
                "recovery_seconds": _recovery_seconds(data),
                "similarity": round(similarity, 2),
            }
        )

    scored.sort(key=lambda s: s["similarity"], reverse=True)
    return scored[:limit]
