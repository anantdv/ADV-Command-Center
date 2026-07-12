from typing import Literal

from app.schemas.common import CamelModel


class NotificationTickerItem(CamelModel):
    id: str
    type: Literal["approval", "invoice", "issue", "task", "stock", "system", "event"]
    label: str
    message: str
    priority: Literal["low", "medium", "high", "critical"] = "low"
    route: str | None = None
    created_at: str | None = None
