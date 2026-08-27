"""The Safety Policy Engine.

Extends the flat action whitelist (safety.py) with per-service risk
overrides, environment/criticality-based escalation, an explicit
"requires approval" override list, execution rate limiting, and the
global autonomy mode + kill switch. This is the single function
orchestrator.py calls to decide what happens to a proposed action — it
never consults safety.py or settings_store.py directly.
"""

from datetime import datetime, timedelta, timezone

from google.cloud import firestore

from app.agent.safety import risk_for_action
from app.incidents_store import list_remediations_for_service
from app.models import PolicyEvaluation, Risk
from app.settings_store import get_global_settings, get_service_profile

RATE_LIMIT_WINDOW_MINUTES = 10
RATE_LIMIT_MAX_EXECUTIONS = 2


def evaluate_policy(db: firestore.Client, service_id: str, action: str) -> PolicyEvaluation:
    base_risk = risk_for_action(action)
    if base_risk is None:
        return PolicyEvaluation(
            decision="blocked",
            risk=None,
            reason=f"'{action}' is not on the safe-remediation whitelist — never auto/approve-executed.",
        )

    settings = get_global_settings(db)
    profile = get_service_profile(db, service_id)
    risk: Risk = base_risk
    reasons = [f"base risk for '{action}' is {base_risk}"]
    service_allows_auto = True

    if profile is not None:
        override = profile.action_risk_overrides.get(action)
        if override is not None:
            risk = override
            reasons.append(f"service policy for '{service_id}' overrides risk to {override}")

        if profile.environment == "production" and profile.criticality in ("high", "critical") and risk == "low":
            risk = "medium"
            reasons.append(
                f"escalated to medium: '{service_id}' is {profile.criticality} criticality in production"
            )

        if action in profile.actions_requiring_approval:
            if risk == "low":
                risk = "medium"
            reasons.append(f"'{action}' is explicitly listed as approval-required for '{service_id}'")

        if profile.allowed_automatic_actions and action not in profile.allowed_automatic_actions:
            service_allows_auto = False
            reasons.append(f"'{action}' is not in '{service_id}'s' allowed automatic actions")

    rate_limited, rate_reason = _check_rate_limit(db, service_id, action)
    if rate_limited:
        reasons.append(rate_reason)
        return PolicyEvaluation(decision="blocked", risk=risk, reason="; ".join(reasons))

    if settings.autonomy_mode in ("observe_only", "recommend_only"):
        reasons.append(f"autonomy mode is '{settings.autonomy_mode}' — no action is ever executed")
        return PolicyEvaluation(decision="recommend_only", risk=risk, reason="; ".join(reasons))

    if settings.autonomy_mode == "approval_required":
        reasons.append("autonomy mode requires human approval for every action")
        return PolicyEvaluation(decision="requires_approval", risk=risk, reason="; ".join(reasons))

    # autonomous_low_risk: LOW auto-executes unless blocked by kill switch or
    # service policy; everything else needs approval.
    if settings.kill_switch_enabled:
        reasons.append("global kill switch is enabled — automatic execution is disabled")
        return PolicyEvaluation(decision="requires_approval", risk=risk, reason="; ".join(reasons))

    if risk == "low" and service_allows_auto:
        return PolicyEvaluation(decision="auto_execute", risk=risk, reason="; ".join(reasons))

    return PolicyEvaluation(decision="requires_approval", risk=risk, reason="; ".join(reasons))


def _check_rate_limit(db: firestore.Client, service_id: str, action: str) -> tuple[bool, str]:
    """Counts actual executions (apply_safe_remediation was really called),
    regardless of whether the attempt ultimately succeeded — a failed
    execution still hit the target service and should count against the
    limit just as much as a successful one. "blocked"/"proposed"/
    "awaiting_approval"/"rejected" never called apply and don't count."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    records = list_remediations_for_service(db, service_id, action)
    recent_executions = [
        r
        for r in records
        if r.status in ("applied", "verified", "failed")
        and r.created_at
        and datetime.fromisoformat(r.created_at) > window_start
    ]
    if len(recent_executions) >= RATE_LIMIT_MAX_EXECUTIONS:
        return True, (
            f"rate limit exceeded: '{action}' already executed {len(recent_executions)} times on "
            f"'{service_id}' in the last {RATE_LIMIT_WINDOW_MINUTES} minutes (max {RATE_LIMIT_MAX_EXECUTIONS})"
        )
    return False, ""
