"""Actor identity resolution for write endpoints (approve/reject, autonomy
mode, kill switch, service policy edits).

In demo mode (`settings.demo_mode`, true by default in this deployment) any
caller can act as the name they claim in the request body — this is what
lets guest mode work without a backend account system, appropriate for a
hackathon judge quickly reviewing the live demo. In production mode, every
write endpoint instead requires a valid Firebase ID token, and the actor's
identity comes from the verified token — never from anything the client
claims.
"""

from fastapi import HTTPException

from app.config import settings

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        import firebase_admin

        _firebase_app = firebase_admin.initialize_app()
    return _firebase_app


def resolve_actor(authorization: str | None, claimed_name: str | None, fallback: str = "guest") -> str:
    """Returns the name to record as the actor for an audit-trailed action.

    demo_mode=True: trusts `claimed_name` from the request body (or
    `fallback` if none given) — the current deployed behavior.
    demo_mode=False: requires a valid Firebase ID token in `authorization`
    ("Bearer <token>"); the actor is the token's name/email/uid, and
    `claimed_name` is ignored entirely so a caller can't impersonate anyone.
    """
    if settings.demo_mode:
        return claimed_name or fallback

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            401, "Authorization required: provide a Firebase ID token as 'Bearer <token>'."
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        from firebase_admin import auth as firebase_auth

        decoded = firebase_auth.verify_id_token(token, app=_get_firebase_app())
    except Exception as exc:
        raise HTTPException(401, f"Invalid or expired ID token: {exc}") from exc
    return decoded.get("name") or decoded.get("email") or decoded["uid"]
