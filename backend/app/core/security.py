from fastapi import Request


def get_forwarded_session_cookie(request: Request) -> dict[str, str] | None:
    """Return the user's Frappe session without exposing it to application code."""
    sid = request.cookies.get("sid")
    return {"sid": sid} if sid else None


def redact_sensitive(payload: dict | None) -> dict:
    if not payload:
        return {}
    blocked = {"password", "pwd", "api_secret", "token", "authorization", "sid"}
    return {key: "***" if key.lower() in blocked else value for key, value in payload.items()}
