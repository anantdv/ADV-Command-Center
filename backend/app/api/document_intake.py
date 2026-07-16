from fastapi import APIRouter, File, Request, UploadFile

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.crud import ConfirmCrudResponse
from app.schemas.document_intake import DocumentMappingPreview, DocumentUploadResponse, OCRResult, UpdateMappingPreviewRequest
from app.services.document_intake_service import document_intake_service

router = APIRouter(prefix="/document-intake", tags=["Document Intake"])


@router.get("/health", response_model=ApiResponse[dict])
async def document_intake_health() -> ApiResponse[dict]:
    return ApiResponse(data={"status": "ok", "ocr_enabled": True, "max_file_size_mb": document_intake_service.max_file_size_mb})


@router.post("/upload", response_model=ApiResponse[DocumentUploadResponse])
async def upload_document(user: CurrentUserDep, file: UploadFile = File(...)) -> ApiResponse[DocumentUploadResponse]:
    return ApiResponse(data=await document_intake_service.upload(file, user.user))


@router.get("/{intake_id}", response_model=ApiResponse[dict])
async def get_intake(intake_id: str, _: CurrentUserDep) -> ApiResponse[dict]:
    return ApiResponse(data=await document_intake_service.get(intake_id))


@router.post("/{intake_id}/process", response_model=ApiResponse[DocumentMappingPreview])
async def process_intake(intake_id: str, request: Request, user: CurrentUserDep) -> ApiResponse[DocumentMappingPreview]:
    return ApiResponse(data=await document_intake_service.process(intake_id, get_frappe_cookies(request), user.user))


@router.get("/{intake_id}/ocr", response_model=ApiResponse[OCRResult])
async def get_ocr(intake_id: str, _: CurrentUserDep) -> ApiResponse[OCRResult]:
    return ApiResponse(data=await document_intake_service.ocr_result(intake_id))


@router.get("/{intake_id}/extraction-debug", response_model=ApiResponse[dict])
async def extraction_debug(intake_id: str, _: CurrentUserDep) -> ApiResponse[dict]:
    return ApiResponse(data=await document_intake_service.extraction_debug(intake_id))


@router.get("/{intake_id}/mapping-preview", response_model=ApiResponse[DocumentMappingPreview])
async def mapping_preview(intake_id: str, _: CurrentUserDep) -> ApiResponse[DocumentMappingPreview]:
    return ApiResponse(data=await document_intake_service.mapping_preview(intake_id))


@router.put("/{intake_id}/mapping-preview", response_model=ApiResponse[DocumentMappingPreview])
async def update_mapping_preview(intake_id: str, payload: UpdateMappingPreviewRequest, request: Request, user: CurrentUserDep) -> ApiResponse[DocumentMappingPreview]:
    return ApiResponse(data=await document_intake_service.update_mapping_preview(intake_id, payload, get_frappe_cookies(request), user.user))


@router.post("/{intake_id}/confirm-create", response_model=ApiResponse[ConfirmCrudResponse])
async def confirm_create(intake_id: str, request: Request, user: CurrentUserDep) -> ApiResponse[ConfirmCrudResponse]:
    return ApiResponse(data=await document_intake_service.confirm_create(intake_id, get_frappe_cookies(request), user.user))


@router.post("/{intake_id}/cancel", response_model=ApiResponse[bool])
async def cancel_intake(intake_id: str, user: CurrentUserDep) -> ApiResponse[bool]:
    return ApiResponse(data=await document_intake_service.cancel(intake_id, user.user))
