from app.agent.tools import extract_error_patterns
from app.models import LogEntry


def _entry(message: str, level: str = "error") -> LogEntry:
    return LogEntry(id="x", timestamp="2026-01-01T00:00:00Z", level=level, message=message)


def test_extract_error_patterns_groups_by_normalized_message():
    logs = [
        _entry("Upstream payments-api returned 500 for 12 consecutive requests."),
        _entry("Upstream payments-api returned 500 for 7 consecutive requests."),
        _entry("Circuit breaker OPEN.", level="warn"),
    ]
    patterns = extract_error_patterns(logs)
    assert len(patterns) == 2
    top = patterns[0]
    assert top.count == 2
    assert top.level == "error"
    assert 0.5 < top.confidence <= 0.99


def test_extract_error_patterns_ignores_info_logs():
    logs = [_entry("Service started.", level="info"), _entry("Something broke.", level="error")]
    patterns = extract_error_patterns(logs)
    assert len(patterns) == 1
    assert patterns[0].pattern == "Something broke."


def test_extract_error_patterns_empty_input():
    assert extract_error_patterns([]) == []
