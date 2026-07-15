from __future__ import annotations

from app.utils.ids import new_id


def api_error(
    code: str,
    user_message: str,
    debug_message: str | None = None,
    *,
    include_debug: bool = False,
    details: dict | None = None,
) -> dict:
    """Consistent JSON error payload for browser clients and proxy debugging."""
    debug_id = new_id("dbg")
    error = {
        "code": code,
        "user_message": user_message,
        "debug_id": debug_id,
    }
    if include_debug and debug_message:
        error["debug_message"] = debug_message
    return {
        "success": False,
        "message": user_message,
        "details": details or {},
        "error": error,
    }
