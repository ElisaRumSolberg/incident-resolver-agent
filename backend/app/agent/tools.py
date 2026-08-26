"""Raw tool implementations.

These call the monitored demo service over HTTP and do deterministic
log grouping. They are wrapped as ADK FunctionTools in adk_agent.py so
the LLM can decide when to call them, but the logic here has no LLM
involvement — it's plain, testable Python.
"""

import re
from collections import Counter
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.models import ConfigSnapshot, ErrorPattern, HealthResult, LogEntry

_TIMEOUT = httpx.Timeout(10.0)


def _service_url(service_id: str) -> str:
    # MVP has a single monitored demo service; service_id is accepted for
    # forward-compatibility with the multi-service stretch goal.
    return settings.demo_service_url


def check_service_health(service_id: str) -> HealthResult:
    url = _service_url(service_id)
    try:
        resp = httpx.get(f"{url}/health", timeout=_TIMEOUT)
        resp.raise_for_status()
        return HealthResult(**resp.json())
    except httpx.HTTPError as exc:
        return HealthResult(
            status="unhealthy",
            checks={"http": f"unreachable: {exc}"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def read_recent_logs(service_id: str, limit: int = 50) -> list[LogEntry]:
    url = _service_url(service_id)
    resp = httpx.get(f"{url}/logs", params={"limit": limit}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return [LogEntry(**entry) for entry in resp.json()["logs"]]


_NORMALIZE_RE = re.compile(r"\d+")


def extract_error_patterns(logs: list[LogEntry]) -> list[ErrorPattern]:
    """Groups log lines into patterns by normalizing out numbers, so e.g.
    "12 consecutive requests" and "7 consecutive requests" group together.
    Confidence grows with occurrence count and caps at 0.99."""
    relevant = [entry for entry in logs if entry.level in ("error", "warn")]
    normalized_to_original: dict[str, str] = {}
    counter: Counter[str] = Counter()
    level_by_pattern: dict[str, str] = {}

    for entry in relevant:
        key = _NORMALIZE_RE.sub("#", entry.message)
        counter[key] += 1
        normalized_to_original.setdefault(key, entry.message)
        # error outranks warn if both occur for the same pattern
        if level_by_pattern.get(key) != "error":
            level_by_pattern[key] = entry.level

    patterns = []
    for key, count in counter.items():
        confidence = min(0.5 + 0.1 * count, 0.99)
        patterns.append(
            ErrorPattern(
                pattern=normalized_to_original[key],
                count=count,
                level=level_by_pattern[key],
                confidence=round(confidence, 2),
            )
        )
    patterns.sort(key=lambda p: p.count, reverse=True)
    return patterns


def inspect_service_config(service_id: str) -> ConfigSnapshot:
    url = _service_url(service_id)
    resp = httpx.get(f"{url}/config", timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return ConfigSnapshot(revision=data.get("revision"), details=data)


def apply_safe_remediation(service_id: str, action: str) -> dict:
    url = _service_url(service_id)
    resp = httpx.post(f"{url}/admin/incidents/resolve", json={"action": action}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def verify_recovery(service_id: str) -> HealthResult:
    return check_service_health(service_id)
