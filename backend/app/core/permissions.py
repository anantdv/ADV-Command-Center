from typing import Literal

from pydantic import BaseModel, Field


class PermissionResult(BaseModel):
    allowed: bool
    reason: str | None = None
    filtered_fields: list[str] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)
    confirmation_required: bool = False
    risk_level: Literal["low", "medium", "high"] = "low"
    audit_required: bool = True


class PermissionGuard:
    """Central policy boundary; real mode will delegate to Frappe permissions."""

    def __init__(self, roles: list[str] | None = None):
        self.roles = roles or []

    async def check(
        self,
        user: str,
        action: str,
        doctype: str | None = None,
        record_name: str | None = None,
        fields: list[str] | None = None,
        payload: dict | None = None,
    ) -> PermissionResult:
        del user, record_name
        action_key = action.lower()
        doctype_key = (doctype or "").lower()
        requested_fields = fields or list((payload or {}).keys())

        if any(term in doctype_key for term in ("payroll", "salary")) and "HR Manager" not in self.roles:
            return PermissionResult(allowed=False, reason="HR Manager role is required.", blocked_fields=requested_fields, risk_level="high")

        high_risk = action_key in {"delete", "submit", "cancel"} or any(term in doctype_key for term in ("payment entry", "journal entry"))
        if high_risk:
            return PermissionResult(allowed=False, reason="This high-risk operation is not enabled in the controlled draft stage.", confirmation_required=False, risk_level="high", blocked_fields=requested_fields)
        if action_key in {"create", "create_draft", "update", "write"}:
            return PermissionResult(allowed=True, confirmation_required=True, risk_level="medium", filtered_fields=requested_fields)
        if action_key == "export":
            return PermissionResult(allowed=True, risk_level="medium", filtered_fields=requested_fields)
        if action_key in {"read", "list", "get", "schema"}:
            return PermissionResult(allowed=True, risk_level="low", filtered_fields=requested_fields)
        return PermissionResult(allowed=True, risk_level="medium", filtered_fields=requested_fields)
        # TODO: Replace mock policy decisions with companion Frappe permission API checks.
