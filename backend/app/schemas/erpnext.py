from typing import Any

from pydantic import AliasChoices, Field

from app.schemas.common import CamelModel, PermissionMeta


class CurrentUserContext(CamelModel):
    user: str
    full_name: str
    company: str | None = None
    company_currency: str = "INR"
    allowed_companies: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    timezone: str = "Asia/Kolkata"
    language: str = "en"
    is_guest: bool = False
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)


class AllowedDoctype(CamelModel):
    name: str
    label: str
    module: str
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)


class DoctypeSchemaRequest(CamelModel):
    doctype: str


class FieldSchema(CamelModel):
    fieldname: str
    label: str
    fieldtype: str
    options: str | None = None
    required: bool = False
    read_only: bool = False
    hidden: bool = False
    permlevel: int = 0
    depends_on: str | None = None
    fetch_from: str | None = None
    default: Any = None
    description: str | None = None


class DoctypeSchema(CamelModel):
    doctype: str
    module: str | None = None
    is_submittable: bool = False
    fields: list[FieldSchema]
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)


class ListRecordsRequest(CamelModel):
    doctype: str
    filters: list[Any] | dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=lambda: ["name"])
    limit_start: int = Field(0, ge=0)
    limit: int = Field(
        20,
        ge=1,
        le=500,
        validation_alias=AliasChoices("limit", "limitPageLength", "limit_page_length"),
    )
    order_by: str | None = None

    @property
    def limit_page_length(self) -> int:
        return self.limit


class ListRecordsResponse(CamelModel):
    records: list[dict[str, Any]]
    total: int
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)


class GetRecordRequest(CamelModel):
    doctype: str
    name: str = Field(validation_alias=AliasChoices("name", "recordName", "record_name"))
    fields: list[str] = Field(default_factory=lambda: ["name"])


class RecordMutationRequest(CamelModel):
    doctype: str
    name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("name", "recordName", "record_name"),
    )
    data: dict[str, Any] = Field(validation_alias=AliasChoices("data", "values"))
    confirmed: bool = False

    @property
    def values(self) -> dict[str, Any]:
        return self.data


class RecordResponse(CamelModel):
    record: dict[str, Any]
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)


class DocumentDetailResponse(CamelModel):
    doctype: str
    name: str
    title: str | None = None
    docstatus: int | None = None
    status: str | None = None
    workflow_state: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)
    available_workflow_actions: list[dict[str, Any]] = Field(default_factory=list)
    permission: dict[str, Any] | None = None
