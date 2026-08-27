from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app import auth
from app.config import settings


def test_demo_mode_trusts_the_claimed_name(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    assert auth.resolve_actor(None, "Elisa", fallback="guest") == "Elisa"


def test_demo_mode_falls_back_when_no_name_claimed(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    assert auth.resolve_actor(None, None, fallback="guest") == "guest"


def test_non_demo_mode_rejects_missing_authorization(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    with pytest.raises(HTTPException) as exc_info:
        auth.resolve_actor(None, "Someone I Claim To Be", fallback="guest")
    assert exc_info.value.status_code == 401


def test_non_demo_mode_rejects_a_non_bearer_header(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    with pytest.raises(HTTPException) as exc_info:
        auth.resolve_actor("Basic abc123", "Someone I Claim To Be", fallback="guest")
    assert exc_info.value.status_code == 401


def test_non_demo_mode_rejects_an_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    with patch("firebase_admin.auth.verify_id_token", side_effect=ValueError("bad token")):
        with pytest.raises(HTTPException) as exc_info:
            auth.resolve_actor("Bearer not-a-real-token", None, fallback="guest")
    assert exc_info.value.status_code == 401


def test_non_demo_mode_ignores_the_claimed_name_and_uses_the_verified_token(monkeypatch):
    """The whole point: a caller cannot impersonate someone else by just
    putting a different name in the request body — the verified token wins."""
    monkeypatch.setattr(settings, "demo_mode", False)
    with patch(
        "firebase_admin.auth.verify_id_token",
        return_value={"name": "Real Verified User", "email": "real@example.com", "uid": "abc"},
    ):
        actor = auth.resolve_actor("Bearer a-real-token", "Google SRE Admin", fallback="guest")
    assert actor == "Real Verified User"
    assert actor != "Google SRE Admin"


def test_non_demo_mode_falls_back_to_email_then_uid_if_no_name(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    with patch(
        "firebase_admin.auth.verify_id_token",
        return_value={"email": "real@example.com", "uid": "abc"},
    ):
        assert auth.resolve_actor("Bearer x", None, fallback="guest") == "real@example.com"

    with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "abc"}):
        assert auth.resolve_actor("Bearer x", None, fallback="guest") == "abc"
