from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.datetime import utc_now


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AIConversation(TimestampMixin, Base):
    __tablename__ = "ai_conversations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    messages: Mapped[list["AIMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(TimestampMixin, Base):
    __tablename__ = "ai_messages"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("ai_conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    parts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    conversation: Mapped[AIConversation] = relationship(back_populates="messages")


class AIToolCall(TimestampMixin, Base):
    __tablename__ = "ai_tool_calls"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    tool_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AIGeneratedFile(TimestampMixin, Base):
    __tablename__ = "ai_generated_files"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(64))
    path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    generated_by: Mapped[str] = mapped_column(String(255))


class AIDashboard(TimestampMixin, Base):
    __tablename__ = "ai_dashboards"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner: Mapped[str] = mapped_column(String(255))


class AIDashboardWidget(TimestampMixin, Base):
    __tablename__ = "ai_dashboard_widgets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dashboard_id: Mapped[str] = mapped_column(ForeignKey("ai_dashboards.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    widget_type: Mapped[str] = mapped_column(String(64))
    config: Mapped[dict] = mapped_column(JSON, default=dict)


class AITrainingResult(TimestampMixin, Base):
    __tablename__ = "ai_training_results"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), index=True)
    assessment_id: Mapped[str] = mapped_column(String(128))
    score: Mapped[float] = mapped_column(Float)


class AISupportTicket(TimestampMixin, Base):
    __tablename__ = "ai_support_tickets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="Open")


class AIAuditLog(Base):
    __tablename__ = "ai_audit_logs"
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    agent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    doctype: Mapped[str | None] = mapped_column(String(128), nullable=True)
    record_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowed: Mapped[bool] = mapped_column(Boolean)
    risk_level: Mapped[str] = mapped_column(String(16))
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
