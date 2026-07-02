from typing import Literal

from app.schemas.common import CamelModel, PermissionMeta


class TicketCreate(CamelModel):
    subject: str
    description: str
    priority: Literal["High", "Medium", "Low"] = "Medium"


class Ticket(CamelModel):
    id: str
    subject: str
    priority: Literal["High", "Medium", "Low"]
    status: Literal["Open", "In Progress", "Resolved"]
    assigned_to: str
    created: str
    permissions: PermissionMeta


class AiHelpRequest(CamelModel):
    message: str
    module: str | None = None


class AiHelpResponse(CamelModel):
    answer: str
    suggested_actions: list[str]
    create_ticket_recommended: bool
