from typing import Any, Literal

from pydantic import BaseModel, Field


class MissingField(BaseModel):
    fieldname: str
    label: str
    fieldtype: str = "Data"
    options: str | None = None
    required: bool = True


class CrudPreviewRequest(BaseModel):
    operation: Literal["create", "update"]
    doctype: str
    record_name: str | None = None
    data: dict[str, Any]
    conversation_id: str | None = None
    message_id: str | None = None


class CrudPreviewResponse(BaseModel):
    operation: Literal["create", "update"]
    doctype: str
    record_name: str | None = None
    data: dict[str, Any]
    missing_fields: list[MissingField] = Field(default_factory=list)
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any] | None = None
    permission: dict[str, Any] | None = None
    risk_level: Literal["medium", "high"] = "medium"
    confirmation_required: bool = True
    confirmation_id: str | None = None


class ConfirmCrudRequest(BaseModel):
    confirmation_id: str


class ConfirmCrudResponse(BaseModel):
    operation: Literal["create", "update"]
    doctype: str
    record_name: str
    status: str | None = None
    message: str
    data: dict[str, Any] | None = None


class ContinueCrudRequest(CrudPreviewRequest):
    pass


class CancelCrudResponse(BaseModel):
    cancelled: bool = True
