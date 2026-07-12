from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.notifications import NotificationTickerItem
from app.services.erpnext_service import ERPNextService
from app.services.workflow_service import workflow_service
from app.utils.datetime import utc_now


class NotificationService:
    def __init__(self, client: FrappeClient | None = None):
        self.client = client

    def _client(self) -> FrappeClient:
        return self.client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)

    async def ticker(self, cookies: dict | None = None, user: str = "unknown") -> list[NotificationTickerItem]:
        if settings.use_mock_data:
            return self._mock()
        erp = ERPNextService(self._client())
        items: list[NotificationTickerItem] = []
        try:
            pending = await workflow_service.list_pending_approvals(cookies=cookies, limit=25, user=user)
            if pending.total:
                items.append(NotificationTickerItem(id="ticker_pending_approvals", type="approval", label="Approvals", message=f"{pending.total} documents waiting for review", priority="high", route="/command-center?prompt=show%20my%20pending%20approvals&autoRun=true", created_at=utc_now().isoformat()))
        except Exception:
            pass
        async def count(doctype: str, filters: dict, fields: list[str] | None = None) -> int | None:
            try:
                return len((await erp.list_records(doctype, filters, fields or ["name"], 100, cookies=cookies)).records)
            except Exception:
                return None
        overdue = await count("Sales Invoice", {"status": "Overdue"})
        if overdue:
            items.append(NotificationTickerItem(id="ticker_overdue_invoices", type="invoice", label="Receivables", message=f"{overdue} overdue sales invoices", priority="high", route="/command-center?prompt=show%20overdue%20sales%20invoices&autoRun=true", created_at=utc_now().isoformat()))
        issues = await count("Issue", {"status": "Open"})
        if issues:
            items.append(NotificationTickerItem(id="ticker_open_issues", type="issue", label="Issues", message=f"{issues} open support issues", priority="medium", route="/modules/support", created_at=utc_now().isoformat()))
        tasks = await count("Task", {"status": "Open"})
        if tasks:
            items.append(NotificationTickerItem(id="ticker_open_tasks", type="task", label="Tasks", message=f"{tasks} open tasks", priority="low", route="/modules/projects", created_at=utc_now().isoformat()))
        if not items:
            items.append(NotificationTickerItem(id="ticker_system_ok", type="system", label="System", message="No urgent notifications", priority="low", created_at=utc_now().isoformat()))
        return items[:8]

    @staticmethod
    def _mock() -> list[NotificationTickerItem]:
        now = utc_now().isoformat()
        return [
            NotificationTickerItem(id="ticker_pending_approvals", type="approval", label="Approvals", message="3 documents waiting for review", priority="high", route="/command-center?prompt=show%20my%20pending%20approvals&autoRun=true", created_at=now),
            NotificationTickerItem(id="ticker_overdue_invoices", type="invoice", label="Receivables", message="4 overdue sales invoices", priority="medium", route="/command-center?prompt=show%20overdue%20sales%20invoices&autoRun=true", created_at=now),
            NotificationTickerItem(id="ticker_open_issues", type="issue", label="Support", message="2 new customer issues", priority="high", route="/modules/support", created_at=now),
            NotificationTickerItem(id="ticker_stock", type="stock", label="Stock", message="Low stock alert for 2 items", priority="low", route="/modules/stock", created_at=now),
        ]


notification_service = NotificationService()
