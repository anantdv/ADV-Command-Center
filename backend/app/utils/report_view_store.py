from __future__ import annotations

from app.schemas.report_composer import SaveReportViewRequest, SavedReportView
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class ReportViewStore:
    """Small local repository for saved report configurations.

    It stores report plans only; report result rows are intentionally never
    persisted as part of a saved view.
    """

    _views: dict[str, SavedReportView] = {}

    async def save(self, request: SaveReportViewRequest, user: str) -> SavedReportView:
        view = SavedReportView(
            view_id=new_id("view"),
            name=request.name,
            description=request.description,
            plan=request.plan,
            visibility=request.visibility,
            allowed_roles=request.allowed_roles,
            created_by=user or "unknown",
            created_at=utc_now().isoformat(),
        )
        self._views[view.view_id] = view
        return view

    async def list(self, user: str, roles: list[str]) -> list[SavedReportView]:
        return [view for view in self._views.values() if self._allowed(view, user, roles)]

    async def get(self, view_id: str, user: str, roles: list[str]) -> SavedReportView | None:
        view = self._views.get(view_id)
        if not view or not self._allowed(view, user, roles):
            return None
        return view

    async def delete(self, view_id: str, user: str, roles: list[str]) -> bool:
        view = await self.get(view_id, user, roles)
        if not view:
            return False
        self._views.pop(view_id, None)
        return True

    @staticmethod
    def _allowed(view: SavedReportView, user: str, roles: list[str]) -> bool:
        if view.created_by == user or "System Manager" in roles:
            return True
        return view.visibility == "role_based" and bool(set(view.allowed_roles) & set(roles))


report_view_store = ReportViewStore()
