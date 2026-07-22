from typing import Any, Literal

from pydantic import BaseModel, Field


ResolutionStatus = Literal["resolved", "needs_selection", "no_match", "invalid"]


class EntitySearchContext(BaseModel):
    parent_doctype: str | None = None
    company: str | None = None
    supplier: str | None = None
    customer: str | None = None
    warehouse: str | None = None


class EntitySearchRequest(BaseModel):
    doctype: str
    query: str
    search_fields: list[str] = Field(default_factory=list)
    context: EntitySearchContext = Field(default_factory=EntitySearchContext)
    limit: int = Field(default=8, ge=1, le=20)


class EntityMatch(BaseModel):
    value: str
    label: str
    description: str | None = None
    match_type: str
    score: float
    disabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntitySearchResponse(BaseModel):
    doctype: str
    query: str
    matches: list[EntityMatch] = Field(default_factory=list)
    has_more: bool = False


class ChildRowResolution(BaseModel):
    row_id: str
    source_text: str
    status: ResolutionStatus
    extracted: dict[str, Any] = Field(default_factory=dict)
    link_field: str
    query: str
    matches: list[EntityMatch] = Field(default_factory=list)
    selected_value: str | None = None
    message: str | None = None


class ChildRowsResolutionPart(BaseModel):
    type: Literal["child_rows_resolution_required"] = "child_rows_resolution_required"
    draft_session_id: str
    doctype: str
    table_field: str
    rows: list[ChildRowResolution]
