from datetime import date

from app.db.seed import FULL_PERMISSION
from app.schemas.common import PermissionMeta
from app.schemas.support import AiHelpRequest, AiHelpResponse, Ticket, TicketCreate
from app.utils.ids import new_id


class SupportService:
    def __init__(self) -> None:
        permission = PermissionMeta(**FULL_PERMISSION)
        self.tickets = [
            Ticket(id="SUP-2026-0148", subject="Unable to submit Sales Invoice", priority="High", status="In Progress", assigned_to="Rahul Mehta", created="01 Jul 2026", permissions=permission),
            Ticket(id="SUP-2026-0142", subject="Payment Entry not reflecting", priority="Medium", status="Open", assigned_to="AI Triage", created="30 Jun 2026", permissions=permission),
            Ticket(id="SUP-2026-0133", subject="Stock Ledger mismatch", priority="High", status="Resolved", assigned_to="Sneha Rao", created="28 Jun 2026", permissions=permission),
        ]

    async def list_tickets(self) -> list[Ticket]: return self.tickets

    async def create_ticket(self, request: TicketCreate) -> Ticket:
        ticket = Ticket(id=new_id("SUP"), subject=request.subject, priority=request.priority, status="Open", assigned_to="AI Triage", created=date.today().isoformat(), permissions=PermissionMeta(**FULL_PERMISSION))
        self.tickets.insert(0, ticket)
        return ticket

    async def ai_help(self, request: AiHelpRequest) -> AiHelpResponse:
        return AiHelpResponse(answer=f"I checked common causes for “{request.message}”. Review document status and user permissions first.", suggested_actions=["Check document status", "Review user permissions", "Create support ticket"], create_ticket_recommended=False)


support_service = SupportService()
