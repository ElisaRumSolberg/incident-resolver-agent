"""The observe -> reason -> act -> verify -> re-plan loop.

This module owns all state transitions. The ADK agent (app.agent.adk_agent)
only produces a diagnosis + proposed action; every decision about whether
that action is safe to run, whether it needs approval, and what to do if
it fails is made here deterministically against the safety whitelist.
"""

from datetime import datetime, timezone

from google.cloud import firestore

from app.agent.activity_log import log_event
from app.agent.adk_agent import run_diagnosis
from app.agent.safety import is_auto_executable, risk_for_action
from app.agent.similarity import find_similar_incidents
from app.agent.tools import apply_safe_remediation, verify_recovery
from app.incidents_store import (
    get_incident,
    get_remediation,
    new_remediation,
    update_incident,
    update_remediation,
)
from app.models import Incident, RemediationRecord

MAX_ATTEMPTS = 3


async def investigate(db: firestore.Client, incident: Incident) -> tuple[Incident, RemediationRecord]:
    log_event(db, incident.id, "investigation_started", f"Investigating incident on {incident.service_id}.")
    # Avoid repeating both actions that were actually tried and failed, and
    # actions a human already rejected — but the two are tracked separately
    # (see reject_remediation) so a rejection doesn't masquerade as a failed
    # attempt when the incident later escalates.
    proposal = await run_diagnosis(incident.service_id, incident.attempted_actions + incident.rejected_actions)
    log_event(
        db,
        incident.id,
        "diagnosis",
        f"Root cause: {proposal.root_cause} (confidence {proposal.confidence:.0%}). "
        f"Proposed action: {proposal.action}.",
    )
    similar = find_similar_incidents(db, proposal.root_cause, incident.service_id, incident.id)
    update_incident(
        db,
        incident.id,
        current_hypothesis=proposal.root_cause,
        root_cause=proposal.root_cause,
        confidence=proposal.confidence,
        severity=proposal.severity,
        next_action=proposal.action,
        similar_incidents=similar,
    )
    if similar:
        top = similar[0]
        log_event(
            db,
            incident.id,
            "similar_incident_found",
            f"Similar incident found: {top['similarity']:.0%} match with "
            f"{top['incident_id'][:8]} (fixed with {top['action']}).",
        )
    risk = risk_for_action(proposal.action)

    if risk is None:
        remediation = new_remediation(
            db, incident.id, proposal.action, risk="high", status="blocked", reason=proposal.reason
        )
        update_incident(db, incident.id, status="escalation_required")
        log_event(
            db,
            incident.id,
            "escalation",
            f"Proposed action '{proposal.action}' is not a whitelisted safe action. Escalating to a human.",
        )
        return get_incident(db, incident.id), remediation

    if is_auto_executable(risk):
        remediation = new_remediation(
            db, incident.id, proposal.action, risk=risk, status="approved", reason=proposal.reason
        )
        log_event(
            db, incident.id, "auto_approved", f"'{proposal.action}' is LOW risk — executing automatically."
        )
        return await _apply_and_verify(db, incident, remediation)

    remediation = new_remediation(
        db, incident.id, proposal.action, risk=risk, status="awaiting_approval", reason=proposal.reason
    )
    update_incident(db, incident.id, status="awaiting_approval")
    log_event(
        db, incident.id, "awaiting_approval", f"'{proposal.action}' is MEDIUM risk — waiting for human approval."
    )
    return get_incident(db, incident.id), remediation


async def _apply_and_verify(
    db: firestore.Client, incident: Incident, remediation: RemediationRecord
) -> tuple[Incident, RemediationRecord]:
    update_incident(db, incident.id, status="remediating")
    log_event(db, incident.id, "remediation_applying", f"Applying '{remediation.action}'.")

    try:
        result = apply_safe_remediation(incident.service_id, remediation.action)
    except Exception as exc:
        # The target service being unreachable, already fixed by a
        # concurrent incident, or returning an unexpected error must never
        # crash the request — it's just a failed attempt, handled the same
        # way a failed verification is.
        log_event(db, incident.id, "remediation_apply_failed", f"Applying '{remediation.action}' failed: {exc}")
        return await _handle_failed_attempt(db, incident, remediation)

    if isinstance(result, dict) and result.get("status") == "no_effect":
        # The target's state didn't actually match this action anymore (e.g.
        # a concurrent incident already resolved it differently) — treat as
        # a failed attempt rather than silently claiming success.
        log_event(
            db,
            incident.id,
            "remediation_apply_failed",
            f"'{remediation.action}' had no effect — the service's failure state had already changed.",
        )
        return await _handle_failed_attempt(db, incident, remediation)

    update_remediation(db, remediation.id, status="applied")

    update_incident(db, incident.id, status="verifying")
    log_event(db, incident.id, "verifying", "Re-checking service health.")
    health = verify_recovery(incident.service_id)

    if health.status == "healthy":
        update_remediation(db, remediation.id, status="verified", verified=True)
        update_incident(
            db,
            incident.id,
            status="resolved",
            resolved_at=datetime.now(timezone.utc).isoformat(),
            attempted_actions=firestore.ArrayUnion([remediation.action]),
        )
        log_event(db, incident.id, "resolved", "Service healthy again. Incident resolved.")
        return get_incident(db, incident.id), get_remediation(db, remediation.id)

    return await _handle_failed_attempt(db, incident, remediation)


async def _handle_failed_attempt(
    db: firestore.Client, incident: Incident, remediation: RemediationRecord
) -> tuple[Incident, RemediationRecord]:
    """Marks one remediation attempt as failed, then either re-plans with a
    different action or escalates to a human once MAX_ATTEMPTS is hit."""
    update_remediation(db, remediation.id, status="failed")
    log_event(
        db, incident.id, "remediation_failed", f"'{remediation.action}' did not resolve the incident. Re-planning."
    )
    attempted = incident.attempted_actions + [remediation.action]
    update_incident(db, incident.id, attempted_actions=attempted, status="investigating")
    incident = get_incident(db, incident.id)

    if len(attempted) >= MAX_ATTEMPTS:
        update_incident(db, incident.id, status="escalation_required")
        log_event(
            db,
            incident.id,
            "escalation",
            f"Reached max remediation attempts ({MAX_ATTEMPTS}). Escalating to a human.",
        )
        return get_incident(db, incident.id), get_remediation(db, remediation.id)

    return await investigate(db, incident)


async def approve_remediation(
    db: firestore.Client, incident_id: str, remediation_id: str
) -> tuple[Incident, RemediationRecord]:
    incident = get_incident(db, incident_id)
    remediation = get_remediation(db, remediation_id)
    if incident is None or remediation is None:
        raise ValueError("Incident or remediation not found.")
    if remediation.status != "awaiting_approval":
        raise ValueError("Remediation is not awaiting approval.")

    update_remediation(db, remediation.id, status="approved")
    log_event(db, incident.id, "approved", f"Human approved '{remediation.action}'.")
    remediation = get_remediation(db, remediation_id)
    return await _apply_and_verify(db, incident, remediation)


async def reject_remediation(
    db: firestore.Client, incident_id: str, remediation_id: str
) -> tuple[Incident, RemediationRecord]:
    incident = get_incident(db, incident_id)
    remediation = get_remediation(db, remediation_id)
    if incident is None or remediation is None:
        raise ValueError("Incident or remediation not found.")
    if remediation.status != "awaiting_approval":
        raise ValueError("Remediation is not awaiting approval.")

    update_remediation(db, remediation.id, status="rejected")
    log_event(db, incident.id, "rejected", f"Human rejected '{remediation.action}'. Re-planning.")
    # Rejections are tracked separately from attempted_actions — a human
    # declining a proposal is not the same claim as "this was tried and
    # failed," and must not silently count toward the failed-attempt
    # escalation threshold used in _handle_failed_attempt.
    rejected = incident.rejected_actions + [remediation.action]
    update_incident(db, incident.id, rejected_actions=rejected, status="investigating")
    incident = get_incident(db, incident.id)

    if len(rejected) >= MAX_ATTEMPTS:
        update_incident(db, incident.id, status="escalation_required")
        log_event(
            db,
            incident.id,
            "escalation",
            f"{MAX_ATTEMPTS} proposed remediations were rejected without any being tried. Escalating to a human.",
        )
        return get_incident(db, incident.id), get_remediation(db, remediation_id)

    return await investigate(db, incident)
