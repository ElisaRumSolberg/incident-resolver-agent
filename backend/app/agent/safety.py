"""The remediation safety whitelist.

This is the one place that decides what risk tier an action belongs to.
The agent's own `risk` opinion is never trusted for execution decisions —
only the action *name* it proposes is looked up here. An action that
isn't in this table (including anything HIGH risk) can never be
auto-executed or approved through the normal flow in this MVP.
"""

from app.models import Risk

ACTION_RISK: dict[str, Risk] = {
    "retry_service": "low",
    "rerun_health_check": "low",
    "gather_logs": "low",
    "restore_env_var": "medium",
    "rollback_revision": "medium",
    "fix_dependency_config": "medium",
}

KNOWN_HIGH_RISK_ACTIONS = {
    "delete_data",
    "rotate_credentials",
    "modify_production_database",
}


def risk_for_action(action: str) -> Risk | None:
    """Returns the whitelisted risk tier for an action, or None if the
    action is unknown/not whitelisted (treated as unsafe to execute)."""
    return ACTION_RISK.get(action)


def requires_approval(risk: Risk) -> bool:
    return risk == "medium"


def is_auto_executable(risk: Risk) -> bool:
    return risk == "low"
