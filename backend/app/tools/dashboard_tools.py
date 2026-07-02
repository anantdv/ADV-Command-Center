from app.schemas.dashboard import DashboardWidgetCreateRequest, DashboardWidgetSource
from app.services.dashboard_service import DashboardService, dashboard_service


class DashboardTools:
    def __init__(self, service: DashboardService | None = None): self.service = service or dashboard_service

    async def pin_result_to_dashboard(self, title: str, widget_type: str, source: dict, chart_config: dict | None = None, layout: dict | None = None, conversation_id: str | None = None, message_id: str | None = None, cookies: dict | None = None, user: str = "unknown") -> dict:
        request = DashboardWidgetCreateRequest(title=title, widget_type=widget_type, source=DashboardWidgetSource.model_validate(source), chart_config=chart_config, layout=layout, conversation_id=conversation_id, message_id=message_id)
        return (await self.service.create_widget(request, cookies, user, "dashboard_widget_pinned_from_chat")).model_dump()

    async def refresh_dashboard_widget(self, widget_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> dict:
        return (await self.service.refresh_widget(widget_id, cookies, user, roles)).model_dump()
