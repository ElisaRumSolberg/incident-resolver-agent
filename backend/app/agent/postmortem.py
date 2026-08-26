"""Auto-generated postmortems for resolved incidents.

One grounded Gemini call, cached forever per incident (postmortems don't
change once an incident is resolved). Grounded strictly in the incident's
own recorded fields and timeline — no outside knowledge, no invented
follow-up actions.
"""

from google import genai
from google.cloud import firestore

from app.config import settings
from app.models import Incident

_client: genai.Client | None = None


def _gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return _client


POSTMORTEM_PROMPT = """Write a short postmortem for this resolved incident.
Use ONLY the facts given below — do not invent details, causes, or follow-up
work that isn't implied by the recorded timeline.

Service: {service_id}
Severity: {severity}
Root cause: {root_cause}
Confidence: {confidence}
Actions attempted (in order): {attempted_actions}
Recovery time: {recovery_seconds} seconds
Timeline:
{timeline}

Write 3-5 short sentences: what happened, what the agent found, what fixed
it, and one sentence of forward-looking advice grounded in the root cause
(e.g. suggest monitoring the same signal, not a generic platitude). Plain
prose, no headers, no bullet points.
"""


async def generate_postmortem(db: firestore.Client, incident: Incident, events: list[dict]) -> dict:
    doc_ref = db.collection("postmortems").document(incident.id)
    cached = doc_ref.get()
    if cached.exists:
        return cached.to_dict()

    recovery_seconds = None
    if incident.resolved_at and incident.started_at:
        from datetime import datetime

        start = datetime.fromisoformat(incident.started_at)
        end = datetime.fromisoformat(incident.resolved_at)
        recovery_seconds = round((end - start).total_seconds())

    timeline = "\n".join(f"- {e['created_at']}: {e['message']}" for e in events)
    prompt = POSTMORTEM_PROMPT.format(
        service_id=incident.service_id,
        severity=incident.severity or "unknown",
        root_cause=incident.root_cause or "unknown",
        confidence=f"{incident.confidence:.0%}" if incident.confidence is not None else "unknown",
        attempted_actions=", ".join(incident.attempted_actions) or "(none)",
        recovery_seconds=recovery_seconds if recovery_seconds is not None else "unknown",
        timeline=timeline or "(no events recorded)",
    )
    response = await _gemini_client().aio.models.generate_content(
        model=settings.gemini_model, contents=prompt
    )
    summary = (response.text or "").strip()

    record = {
        "incident_id": incident.id,
        "service_id": incident.service_id,
        "summary": summary,
        "recovery_seconds": recovery_seconds,
        "root_cause": incident.root_cause,
    }
    doc_ref.set(record)
    return record
