from datetime import datetime

import structlog
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import AIAuditLog
from app.utils.datetime import utc_now
from app.utils.ids import new_id

logger = structlog.get_logger("audit")


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("audit"))
    user: str
    conversation_id: str | None = None
    action: str
    agent_name: str | None = None
    tool_name: str | None = None
    doctype: str | None = None
    record_name: str | None = None
    allowed: bool
    risk_level: str
    input_summary: str | None = None
    output_summary: str | None = None
    prompt: str | None = None
    intent: str | None = None
    report_name: str | None = None
    filters: dict | None = None
    record_count: int | None = None
    file_id: str | None = None
    file_name: str | None = None
    file_type: str | None = None
    size_bytes: int | None = None
    message_id: str | None = None
    widget_id: str | None = None
    widget_title: str | None = None
    widget_type: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    operation: str | None = None
    allowed_fields: list[str] | None = None
    blocked_fields: list[str] | None = None
    confirmation_id: str | None = None
    status: str | None = None
    provider: str | None = None
    model: str | None = None
    extraction_method: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    fallback_used: bool | None = None
    privacy_blocked: bool | None = None
    privacy_allowed: bool | None = None
    erp_data_sent: bool = False
    source_id: str | None = None
    source_type: str | None = None
    module: str | None = None
    query_hash: str | None = None
    citation_ids: list[str] | None = None
    top_k: int | None = None
    escalation_recommended: bool | None = None
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


async def log_audit_event(event: AuditEvent, db: Session | None = None) -> None:
    """Write an immutable structured audit event and optionally persist it."""
    await logger.ainfo("audit_event", **event.model_dump(mode="json"))
    if db:
        persisted_fields = {column.name for column in AIAuditLog.__table__.columns}
        db.add(AIAuditLog(**{key: value for key, value in event.model_dump().items() if key in persisted_fields}))
        db.commit()
