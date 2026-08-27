"""Deterministic aggregation over Firestore incidents/remediations.

Everything here is plain counting and averaging over already-persisted,
already-decided data (statuses and risk tiers assigned by the safety
whitelist, not by the LLM) — no LLM calls, so these numbers are cheap,
fast, and exactly reproducible.
"""

from datetime import datetime, timezone

from google.cloud import firestore

ACTIVE_STATUSES = {"investigating", "awaiting_approval", "remediating", "verifying"}

ROOT_CAUSE_CATEGORY_BY_ACTION = {
    "restore_env_var": "Configuration errors",
    "rollback_revision": "Bad deployments",
    "fix_dependency_config": "Dependency failures",
    "retry_service": "Transient failures",
    "rerun_health_check": "Transient failures",
    "gather_logs": "Unknown",
    "rotate_credentials": "Security incidents",
}


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts)


def _recent(db: firestore.Client, collection: str, order_field: str, limit: int):
    # Ordered before truncating so a collection past the limit still yields
    # the most recent documents, not an arbitrary/undefined-order subset —
    # an unordered .limit() silently dropped brand-new incidents from the
    # overview once older data pushed past the cap.
    return db.collection(collection).order_by(order_field, direction=firestore.Query.DESCENDING).limit(limit)


def compute_overview(db: firestore.Client) -> dict:
    incidents = [snap.to_dict() for snap in _recent(db, "incidents", "started_at", 500).stream()]
    remediations = [snap.to_dict() for snap in _recent(db, "remediations", "created_at", 1000).stream()]

    active_count = sum(1 for i in incidents if i["status"] in ACTIVE_STATUSES)
    resolved = [i for i in incidents if i["status"] == "resolved"]

    today = datetime.now(timezone.utc).date()
    resolved_today = sum(
        1
        for i in resolved
        if (parsed := _parse(i.get("resolved_at"))) and parsed.date() == today
    )

    recovery_times = []
    for i in resolved:
        start, end = _parse(i.get("started_at")), _parse(i.get("resolved_at"))
        if start and end:
            recovery_times.append((end - start).total_seconds())
    avg_recovery_seconds = round(sum(recovery_times) / len(recovery_times)) if recovery_times else None

    low_risk_verified = sum(1 for r in remediations if r["risk"] == "low" and r["status"] == "verified")
    total_verified = sum(1 for r in remediations if r["status"] == "verified")
    auto_resolved_rate = round(low_risk_verified / total_verified * 100) if total_verified else 0

    awaiting_approval_count = sum(1 for i in incidents if i["status"] == "awaiting_approval")

    return {
        "active_count": active_count,
        "resolved_today": resolved_today,
        "resolved_total": len(resolved),
        "avg_recovery_seconds": avg_recovery_seconds,
        "auto_resolved_rate": auto_resolved_rate,
        "awaiting_approval_count": awaiting_approval_count,
        "incidents_learned_from": len(resolved),
    }


def compute_analytics(db: firestore.Client) -> dict:
    incidents = [snap.to_dict() for snap in _recent(db, "incidents", "started_at", 500).stream()]
    remediations = [snap.to_dict() for snap in _recent(db, "remediations", "created_at", 1000).stream()]
    resolved = [i for i in incidents if i["status"] == "resolved"]

    category_counts: dict[str, int] = {}
    for i in resolved:
        attempted = i.get("attempted_actions") or []
        action = attempted[-1] if attempted else None
        category = ROOT_CAUSE_CATEGORY_BY_ACTION.get(action, "Unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
    total_resolved = len(resolved) or 1
    top_root_causes = [
        {"category": cat, "percent": round(count / total_resolved * 100)}
        for cat, count in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    by_action: dict[str, dict[str, int]] = {}
    for r in remediations:
        action = r["action"]
        bucket = by_action.setdefault(action, {"attempted": 0, "verified": 0})
        if r["status"] in ("applied", "verified", "failed"):
            bucket["attempted"] += 1
        if r["status"] == "verified":
            bucket["verified"] += 1
    remediation_success_rate = [
        {
            "action": action,
            "success_rate": round(counts["verified"] / counts["attempted"] * 100) if counts["attempted"] else 0,
            "attempts": counts["attempted"],
        }
        for action, counts in by_action.items()
        if counts["attempted"] > 0
    ]
    remediation_success_rate.sort(key=lambda r: r["success_rate"], reverse=True)

    return {
        "top_root_causes": top_root_causes,
        "remediation_success_rate": remediation_success_rate,
    }


def compute_safety_stats(db: firestore.Client) -> dict:
    remediations = [snap.to_dict() for snap in _recent(db, "remediations", "created_at", 1000).stream()]

    auto_executed = sum(1 for r in remediations if r["risk"] == "low")
    approved = sum(
        1 for r in remediations if r["risk"] == "medium" and r["status"] in ("approved", "applied", "verified")
    )
    rejected = sum(1 for r in remediations if r["status"] == "rejected")
    awaiting_approval = sum(1 for r in remediations if r["status"] == "awaiting_approval")
    blocked = sum(1 for r in remediations if r["status"] == "blocked")

    return {
        "auto_executed": auto_executed,
        "approved": approved,
        "rejected": rejected,
        "awaiting_approval": awaiting_approval,
        "blocked": blocked,
    }
