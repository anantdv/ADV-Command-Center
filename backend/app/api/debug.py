from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.router_agent import RouterAgent
from app.config import settings
from app.core.exceptions import AppError
from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.llm.extraction_service import LLMExtractionService
from app.llm.privacy_gateway import PrivacyGateway
from app.llm.prompts import ALLOWED_DOCTYPES, ALLOWED_FILE_FORMATS, ALLOWED_REPORTS, ALLOWED_WIDGET_TYPES
from datetime import date
from typing import Any
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.filter_normalizer import normalize_filters, to_frappe_filters
from app.services.query_planner_service import QueryPlannerService
from app.utils.chart_plan_builder import build_chart_from_aggregation
from app.schemas.report_composer import ReportComposerPlanRequest
from app.services.report_composer_service import report_composer_service
from app.utils.report_filter_builder import build_normalized_filters_from_plan
from app.services.command_router_service import command_router_service

router=APIRouter(prefix="/debug",tags=["Development"])


class ExtractIntentRequest(BaseModel):
    message: str = Field(min_length=1,max_length=8000)
    module_context: str | None = None


class NormalizeFiltersRequest(BaseModel):
    doctype: str
    message: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    date_range: dict[str, Any] | None = None


class QueryPlanDebugRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    module_context: str | None = None


class CommandRouteDebugRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    module_context: str | None = None
    date_range: dict[str, Any] | None = None


@router.post("/extract-intent", response_model=ApiResponse[dict])
async def extract_intent(payload: ExtractIntentRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    intent=await RouterAgent().classify(payload.message,payload.module_context)
    safe=intent.model_dump(exclude={"raw_prompt","rows","chart_config"},mode="json")
    outbound = {
        "user_message": payload.message,
        "module_context": payload.module_context,
        "current_date": date.today().isoformat(),
        "allowed_doctypes": ALLOWED_DOCTYPES,
        "allowed_reports": ALLOWED_REPORTS,
        "allowed_file_formats": ALLOWED_FILE_FORMATS,
        "allowed_widget_types": ALLOWED_WIDGET_TYPES,
        "allowed_operations": LLMExtractionService.ALLOWED_OPERATIONS,
    }
    privacy = PrivacyGateway().check_outbound_payload(outbound)
    # Raw output is intentionally not retained by the extraction service. This
    # remains null even in development unless a future encrypted debug sink is
    # explicitly implemented.
    return ApiResponse(data={
        "extraction_method":intent.extraction_method,
        "intent":safe,
        "privacy":{
            "checked":True,
            "allowed":privacy.allowed,
            "detected_categories":privacy.detected_categories,
            "erp_data_sent":False,
        },
        "raw_model_output":None,
    })


@router.post("/normalize-filters", response_model=ApiResponse[dict])
async def normalize_debug(payload: NormalizeFiltersRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    date_range = payload.date_range or (parse_date_range_phrase(payload.message or "") if payload.message else None)
    normalized = normalize_filters(payload.doctype, payload.filters, date_range)
    return ApiResponse(data={
        "doctype": payload.doctype,
        "raw_filters": payload.filters,
        "date_range": date_range,
        "normalized_filters": normalized,
        "frappe_filters": to_frappe_filters(payload.doctype, normalized),
    })


@router.post("/query-plan", response_model=ApiResponse[dict])
async def query_plan_debug(payload: QueryPlanDebugRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    plan = await QueryPlannerService().plan(payload.message, payload.module_context)
    return ApiResponse(data={
        "raw_message": payload.message,
        "query_plan": plan.model_dump(mode="json"),
        "extraction_method": plan.extraction_method,
        "privacy_checked": plan.extraction_method != "rules",
    })


@router.post("/command-route", response_model=ApiResponse[dict])
async def command_route_debug(payload: CommandRouteDebugRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    intent = await command_router_service.route(payload.message, payload.module_context, payload.date_range)
    target = {
        "run_report": "ReportAgent",
        "run_analytics": "AnalyticsAgent",
        "generate_chart": "AnalyticsAgent",
        "workflow_list_pending": "WorkflowAgent",
        "workflow_get_detail": "WorkflowAgent",
        "workflow_apply_action": "WorkflowAgent",
        "get_record_detail": "ERPDataAgent",
        "list_records": "ERPDataAgent",
        "unsupported": "Fallback",
    }.get(intent.intent, "CommandRouter")
    return ApiResponse(data={
        "message": payload.message,
        "intent": intent.model_dump(mode="json"),
        "explicit_context_reference": intent.explicit_context_reference,
        "previous_context_used": intent.uses_previous_result,
        "route_target": target,
    })


@router.post("/aggregation-plan", response_model=ApiResponse[dict])
async def aggregation_plan_debug(payload: QueryPlanDebugRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    plan = await QueryPlannerService().plan(payload.message, payload.module_context)
    aggregation = plan.aggregation
    return ApiResponse(data={
        "query_plan": plan.model_dump(mode="json"),
        "aggregation_plan": aggregation.model_dump(mode="json") if aggregation else None,
        "normalized_filters": aggregation.normalized_filters if aggregation else plan.normalized_filters,
        "required_fields": aggregation.fields if aggregation else plan.fields,
        "chart_plan": build_chart_from_aggregation([], aggregation) if aggregation else None,
    })


@router.post("/report-composer-plan", response_model=ApiResponse[dict])
async def report_composer_plan_debug(payload: ReportComposerPlanRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    plan = await report_composer_service.plan_report(payload)
    return ApiResponse(data={
        "plan": plan.model_dump(mode="json"),
        "validated_plan": plan.model_dump(mode="json"),
        "normalized_filters": build_normalized_filters_from_plan(plan),
        "required_source_fields": report_composer_service._required_source_fields(plan),
        "warnings": plan.warnings,
    })
