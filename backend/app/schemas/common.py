from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ApiResponse(CamelModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorResponse(CamelModel):
    success: bool = False
    message: str
    details: dict = Field(default_factory=dict)


class PermissionMeta(CamelModel):
    allowed: bool = True
    can_read: bool = True
    can_write: bool = False
    can_create: bool = False
    can_delete: bool = False
    can_submit: bool | None = None
    can_cancel: bool | None = None
    can_export: bool | None = None
    reason: str | None = None
    filtered_fields: list[str] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)
    confirmation_required: bool = False
    risk_level: str = "low"
    audit_required: bool = True
