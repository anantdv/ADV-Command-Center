import asyncio
from hashlib import sha256
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.schemas.dashboard import DashboardOverviewResponse, DashboardWidgetCreateRequest, DashboardWidgetData, DashboardWidgetLayout, DashboardWidgetSource, DashboardWidgetUpdateRequest, PinChatResultRequest
from app.utils.widget_data_builder import WidgetDataBuilder
from app.db.models import AIDashboard, AIDashboardWidget
from app.db.base import Base
from app.db.session import SessionLocal, engine


def _source(doctype: str, filters: dict | None = None, fields: list[str] | None = None, group_by: str | None = None, aggregate_field: str | None = None, aggregate_function: str | None = None) -> DashboardWidgetSource:
    return DashboardWidgetSource(source_type="doctype", doctype=doctype, source_name=doctype, filters=filters or {}, fields=fields, group_by=group_by, aggregate_field=aggregate_field, aggregate_function=aggregate_function)


DEFAULT_KPIS = [
    DashboardWidgetCreateRequest(title="Total Customers", widget_type="kpi", source=_source("Customer", aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Total Suppliers", widget_type="kpi", source=_source("Supplier", aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Total Items", widget_type="kpi", source=_source("Item", aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Open Sales Orders", widget_type="kpi", source=_source("Sales Order", {"status":["not in",["Completed","Closed","Cancelled"]]}, aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Open Purchase Orders", widget_type="kpi", source=_source("Purchase Order", {"status":["not in",["Completed","Closed","Cancelled"]]}, aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Overdue Sales Invoices", widget_type="kpi", source=_source("Sales Invoice", {"status":"Overdue"}, aggregate_function="count")),
    DashboardWidgetCreateRequest(title="Outstanding Receivable", widget_type="kpi", source=_source("Sales Invoice", {"outstanding_amount":[">",0]}, ["name","outstanding_amount"], aggregate_field="outstanding_amount", aggregate_function="sum")),
    DashboardWidgetCreateRequest(title="Outstanding Payable", widget_type="kpi", source=_source("Purchase Invoice", {"outstanding_amount":[">",0]}, ["name","outstanding_amount"], aggregate_field="outstanding_amount", aggregate_function="sum")),
]
DEFAULT_CHARTS = [
    DashboardWidgetCreateRequest(title="Sales Invoice Status", widget_type="bar_chart", source=_source("Sales Invoice", fields=["name","status"], group_by="status"), layout=DashboardWidgetLayout(w=6,h=4)),
    DashboardWidgetCreateRequest(title="Purchase Invoice Status", widget_type="donut_chart", source=_source("Purchase Invoice", fields=["name","status"], group_by="status"), layout=DashboardWidgetLayout(w=6,h=4)),
    DashboardWidgetCreateRequest(title="Top Customers by Outstanding", widget_type="bar_chart", source=_source("Sales Invoice", {"outstanding_amount":[">",0]}, ["customer","outstanding_amount"], "customer", "outstanding_amount", "sum"), layout=DashboardWidgetLayout(w=6,h=4)),
    DashboardWidgetCreateRequest(title="Top Suppliers by Outstanding", widget_type="bar_chart", source=_source("Purchase Invoice", {"outstanding_amount":[">",0]}, ["supplier","outstanding_amount"], "supplier", "outstanding_amount", "sum"), layout=DashboardWidgetLayout(w=6,h=4)),
    DashboardWidgetCreateRequest(title="Item Group Distribution", widget_type="pie_chart", source=_source("Item", fields=["name","item_group"], group_by="item_group"), layout=DashboardWidgetLayout(w=6,h=4)),
    DashboardWidgetCreateRequest(title="Open Sales Orders by Status", widget_type="bar_chart", source=_source("Sales Order", {"status":["not in",["Completed","Closed","Cancelled"]]}, ["name","status"], "status"), layout=DashboardWidgetLayout(w=6,h=4)),
]


class DashboardService:
    """User-scoped widget metadata with permission-aware refreshes.

    Metadata uses the FastAPI database fallback until companion list/update/delete methods ship.
    """
    def __init__(self, builder: WidgetDataBuilder | None = None):
        self.builder = builder or WidgetDataBuilder()

    async def get_overview(self, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DashboardOverviewResponse:
        kpis = await self._build_defaults(DEFAULT_KPIS, cookies)
        saved = await self.list_widgets(cookies, user, roles)
        widgets = saved or await self._build_defaults(DEFAULT_CHARTS, cookies)
        await self._audit("dashboard_overview_viewed", user, allowed=True, output=f"{len(kpis)} KPIs, {len(widgets)} widgets")
        return DashboardOverviewResponse(kpis=kpis, widgets=widgets, insights=["Every widget refresh re-checks your current ERPNext permissions.", "Dashboard widgets store source configuration only, never raw ERP records."])

    async def overview(self, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DashboardOverviewResponse:
        return await self.get_overview(cookies, user, roles)

    async def list_widgets(self, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> list[DashboardWidgetData]:
        visible = [item for item in self._load_all() if self._visible(item, user, roles)]
        return await self._refresh_many(visible, cookies, user)

    async def create_widget(self, request: DashboardWidgetCreateRequest, cookies: dict | None = None, user: str = "unknown", event: str = "dashboard_widget_created") -> DashboardWidgetData:
        widget_id = f"widget_{uuid4().hex[:12]}"
        metadata = request.model_dump(mode="json") | {"widget_id":widget_id,"owner":user}
        built = await self.builder.build_widget_data(request, cookies, widget_id)
        self._save(metadata)
        await self._audit(event, user, built, True)
        return built

    async def get_widget(self, widget_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DashboardWidgetData:
        metadata = self._find(widget_id, user, roles)
        return await self._refresh_metadata(metadata, cookies, user)

    async def refresh_widget(self, widget_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DashboardWidgetData:
        widget = await self.get_widget(widget_id, cookies, user, roles)
        await self._audit("dashboard_widget_refreshed", user, widget, True)
        return widget

    async def update_widget(self, widget_id: str, request: DashboardWidgetUpdateRequest, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DashboardWidgetData:
        metadata = self._find(widget_id, user, roles, owner_required=True)
        updates = request.model_dump(exclude_none=True, mode="json")
        metadata.update(updates)
        self._save(metadata, update=True)
        widget = await self._refresh_metadata(metadata, cookies, user)
        await self._audit("dashboard_widget_updated", user, widget, True)
        return widget

    async def delete_widget(self, widget_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> bool:
        metadata = self._find(widget_id, user, roles, owner_required=True)
        self._delete(widget_id)
        await self._audit("dashboard_widget_deleted", user, raw=metadata, allowed=True)
        return True

    async def reorder_widgets(self, layouts: list[dict], cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> bool:
        for item in layouts:
            widget_id = str(item.get("widget_id") or "")
            metadata = self._find(widget_id, user, roles, owner_required=True)
            metadata["layout"] = DashboardWidgetLayout.model_validate(item.get("layout") or item).model_dump()
            self._save(metadata, update=True)
        await self._audit("dashboard_widget_reordered", user, allowed=True, output=f"{len(layouts)} layouts")
        return True

    async def pin_from_chat(self, request: PinChatResultRequest, cookies: dict | None = None, user: str = "unknown") -> DashboardWidgetData:
        create = DashboardWidgetCreateRequest(title=request.title, widget_type=request.widget_type, source=request.source, chart_config=request.chart_config, conversation_id=request.conversation_id, message_id=request.message_id, layout=DashboardWidgetLayout(w=6,h=4) if request.widget_type not in {"kpi","summary_card"} else DashboardWidgetLayout())
        return await self.create_widget(create, cookies, user, "dashboard_widget_pinned_from_chat")

    async def _build_defaults(self, specs: list[DashboardWidgetCreateRequest], cookies: dict | None) -> list[DashboardWidgetData]:
        results = await asyncio.gather(*(self.builder.build_widget_data(spec, cookies, f"default_{index}") for index, spec in enumerate(specs)), return_exceptions=True)
        return [result for result in results if isinstance(result, DashboardWidgetData)]

    async def _refresh_many(self, metadata: list[dict], cookies: dict | None, user: str) -> list[DashboardWidgetData]:
        results = await asyncio.gather(*(self._refresh_metadata(item, cookies, user) for item in metadata), return_exceptions=True)
        output: list[DashboardWidgetData] = []
        for item, result in zip(metadata, results, strict=True):
            if isinstance(result, DashboardWidgetData): output.append(result)
            else:
                await self._audit("dashboard_widget_refresh_failed", user, raw=item, allowed=False, output=type(result).__name__)
                output.append(DashboardWidgetData(**{key:value for key,value in item.items() if key != "owner"}, data=None, permission={"allowed":False}, error="Unable to refresh this widget with your current permissions."))
        return output

    async def _refresh_metadata(self, metadata: dict, cookies: dict | None, user: str) -> DashboardWidgetData:
        try: return await self.builder.build_widget_data(metadata, cookies, metadata["widget_id"])
        except PermissionDenied:
            await self._audit("dashboard_widget_permission_denied", user, raw=metadata, allowed=False)
            raise

    def _find(self, widget_id: str, user: str, roles: list[str] | None, owner_required: bool = False) -> dict:
        metadata = self._load_one(widget_id)
        if not metadata: raise AppError("Dashboard widget was not found.", 404, {"widget_id":widget_id})
        if owner_required and metadata["owner"] != user: raise PermissionDenied("Only the widget owner can modify this widget.")
        if not self._visible(metadata, user, roles): raise PermissionDenied("Dashboard widget access denied.")
        return metadata

    @staticmethod
    def _visible(metadata: dict, user: str, roles: list[str] | None) -> bool:
        if metadata.get("owner") == user: return True
        return metadata.get("visibility") == "role_based" and bool(set(metadata.get("allowed_roles") or []).intersection(roles or []))

    @staticmethod
    def _dashboard_id(user: str) -> str:
        return f"overview_{sha256(user.encode()).hexdigest()[:16]}"

    def _save(self, metadata: dict[str, Any], update: bool = False) -> None:
        owner = metadata["owner"]
        dashboard_id = self._dashboard_id(owner)
        config = {key:value for key,value in metadata.items() if key not in {"widget_id","owner","title","widget_type"}}
        with SessionLocal() as db:
            dashboard = db.get(AIDashboard, dashboard_id)
            if not dashboard:
                dashboard = AIDashboard(id=dashboard_id, name="Overview", owner=owner)
                db.add(dashboard)
                db.flush()
            row = db.get(AIDashboardWidget, metadata["widget_id"])
            if row:
                row.title = metadata["title"]; row.widget_type = metadata["widget_type"]; row.config = config
            else:
                db.add(AIDashboardWidget(id=metadata["widget_id"], dashboard_id=dashboard_id, title=metadata["title"], widget_type=metadata["widget_type"], config=config))
            db.commit()

    @staticmethod
    def _row_metadata(row: AIDashboardWidget, owner: str) -> dict[str, Any]:
        return {**(row.config or {}), "widget_id":row.id, "title":row.title, "widget_type":row.widget_type, "owner":owner}

    def _load_all(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = db.execute(select(AIDashboardWidget, AIDashboard.owner).join(AIDashboard, AIDashboardWidget.dashboard_id == AIDashboard.id)).all()
            return [self._row_metadata(widget, owner) for widget, owner in rows]

    def _load_one(self, widget_id: str) -> dict[str, Any] | None:
        with SessionLocal() as db:
            result = db.execute(select(AIDashboardWidget, AIDashboard.owner).join(AIDashboard, AIDashboardWidget.dashboard_id == AIDashboard.id).where(AIDashboardWidget.id == widget_id)).first()
            return self._row_metadata(result[0], result[1]) if result else None

    @staticmethod
    def _delete(widget_id: str) -> None:
        with SessionLocal() as db:
            row = db.get(AIDashboardWidget, widget_id)
            if row: db.delete(row); db.commit()

    @staticmethod
    def clear_for_tests() -> None:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.query(AIDashboardWidget).delete()
            db.query(AIDashboard).filter(AIDashboard.id.like("overview_%")).delete(synchronize_session=False)
            db.commit()

    async def _audit(self, action: str, user: str, widget: DashboardWidgetData | None = None, allowed: bool = True, raw: dict | None = None, output: str | None = None) -> None:
        data = widget.model_dump() if widget else (raw or {})
        source = data.get("source") or {}
        await log_audit_event(AuditEvent(user=user, action=action, tool_name="dashboard_widget", allowed=allowed, risk_level="medium" if action not in {"dashboard_overview_viewed","dashboard_widget_refreshed"} else "low", doctype=source.get("doctype"), report_name=source.get("report_name"), filters=source.get("filters") or {}, conversation_id=data.get("conversation_id"), message_id=data.get("message_id"), widget_id=data.get("widget_id"), widget_title=data.get("title"), widget_type=data.get("widget_type"), source_type=source.get("source_type"), source_name=source.get("source_name") or source.get("doctype") or source.get("report_name"), input_summary=data.get("title"), output_summary=output))


dashboard_service = DashboardService()
