from typing import Any, Literal

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    name: str
    file_name: str
    file_url: str | None = None
    is_private: bool = True


class CommunicationItem(BaseModel):
    name: str
    subject: str
    sender: str = ""
    recipients: str = ""
    cc: str | None = None
    communication_type: str = "Communication"
    sent_or_received: str = "Received"
    reference_doctype: str | None = None
    reference_name: str | None = None
    creation: str
    status: str | None = None
    has_attachment: bool = False
    preview: str = ""
    unread: bool = False


class CommunicationList(BaseModel):
    items: list[CommunicationItem]
    total: int


class CommunicationMessage(CommunicationItem):
    content: str = ""
    attachments: list[Attachment] = Field(default_factory=list)


class CommunicationThread(BaseModel):
    thread_id: str
    reference_doctype: str | None = None
    reference_name: str | None = None
    messages: list[CommunicationMessage]


class SendEmailRequest(BaseModel):
    to: list[str]
    subject: str
    content: str
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    reference_doctype: str | None = None
    reference_name: str | None = None
    attachments: list[str] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    content: str
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)


class ForwardRequest(ReplyRequest):
    to: list[str]


class LinkRequest(BaseModel):
    reference_doctype: str
    reference_name: str


class EmailTemplateItem(BaseModel):
    name: str
    subject: str | None = None
    response: str | None = None


class RenderTemplateRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)


class AiMailDraftRequest(BaseModel):
    communication_name: str | None = None
    instruction: str
    content: str | None = None


class AiMailDraft(BaseModel):
    action: str
    content: str
    requires_review: bool = True


class ConversionRequest(BaseModel):
    action: Literal["task", "issue", "lead"]


class ActionResult(BaseModel):
    name: str
    doctype: str
    message: str
