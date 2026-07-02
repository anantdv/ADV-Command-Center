import structlog
from fastapi import APIRouter, Query, Request

from app.dependencies import get_frappe_client, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.erpnext import (
    AllowedDoctype,
    CurrentUserContext,
    DoctypeSchema,
    DoctypeSchemaRequest,
    GetRecordRequest,
    ListRecordsRequest,
    ListRecordsResponse,
    RecordMutationRequest,
    RecordResponse,
)
from app.services.erpnext_service import ERPNextService

router = APIRouter(prefix="/erpnext", tags=["ERPNext"])
logger = structlog.get_logger(__name__)


def service() -> ERPNextService:
    return ERPNextService(get_frappe_client())


@router.get("/current-user-context", response_model=ApiResponse[CurrentUserContext])
async def context(request: Request) -> ApiResponse[CurrentUserContext]:
    logger.info("backend_endpoint", endpoint="erpnext.current_user_context")
    return ApiResponse(
        data=await service().get_current_user_context(get_frappe_cookies(request))
    )


@router.get("/allowed-doctypes", response_model=ApiResponse[list[AllowedDoctype]])
async def doctypes(
    request: Request,
    module: str | None = Query(default=None),
) -> ApiResponse[list[AllowedDoctype]]:
    logger.info("backend_endpoint", endpoint="erpnext.allowed_doctypes")
    return ApiResponse(
        data=await service().get_allowed_doctypes(module, get_frappe_cookies(request))
    )


@router.post("/doctype-schema", response_model=ApiResponse[DoctypeSchema])
async def schema(
    payload: DoctypeSchemaRequest,
    request: Request,
) -> ApiResponse[DoctypeSchema]:
    logger.info("backend_endpoint", endpoint="erpnext.doctype_schema")
    return ApiResponse(
        data=await service().get_doctype_schema(
            payload.doctype,
            get_frappe_cookies(request),
        )
    )


@router.post("/list-records", response_model=ApiResponse[ListRecordsResponse])
async def list_records(
    payload: ListRecordsRequest,
    request: Request,
) -> ApiResponse[ListRecordsResponse]:
    logger.info("backend_endpoint", endpoint="erpnext.list_records", doctype=payload.doctype)
    return ApiResponse(
        data=await service().list_records(
            doctype=payload.doctype,
            filters=payload.filters,
            fields=payload.fields,
            limit=payload.limit,
            order_by=payload.order_by,
            cookies=get_frappe_cookies(request),
        )
    )


@router.post("/get-record", response_model=ApiResponse[RecordResponse])
async def get_record(
    payload: GetRecordRequest,
    request: Request,
) -> ApiResponse[RecordResponse]:
    logger.info("backend_endpoint", endpoint="erpnext.get_record", doctype=payload.doctype)
    return ApiResponse(
        data=await service().get_record(
            payload.doctype,
            payload.name,
            payload.fields,
            get_frappe_cookies(request),
        )
    )


@router.post("/create-record", response_model=ApiResponse[RecordResponse])
async def create_record(
    payload: RecordMutationRequest,
    request: Request,
) -> ApiResponse[RecordResponse]:
    from app.core.exceptions import AppError
    raise AppError("Direct record creation is disabled. Use the Command Center confirmation workflow.", 409)


@router.post("/update-record", response_model=ApiResponse[RecordResponse])
async def update_record(
    payload: RecordMutationRequest,
    request: Request,
) -> ApiResponse[RecordResponse]:
    from app.core.exceptions import AppError
    raise AppError("Direct record updates are disabled. Use the Command Center confirmation workflow.", 409)
