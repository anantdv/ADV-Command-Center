from urllib.parse import quote

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.file_generation import GenerateFileRequest, GenerateFileResponse
from app.schemas.library import DeleteResult, LibraryFile, LibraryFileCreate
from app.services.file_generation_service import file_generation_service
from app.services.library_service import library_service

router = APIRouter(prefix="/library", tags=["Library"])


@router.get("/files", response_model=ApiResponse[list[LibraryFile]])
async def files(request: Request, user: CurrentUserDep, category: str | None = Query(None), file_type: str | None = Query(None)) -> ApiResponse[list[LibraryFile]]:
    return ApiResponse(data=await library_service.list_files(file_type or category, get_frappe_cookies(request), user.user, user.roles))


@router.post("/files", response_model=None)
async def create_file(payload: GenerateFileRequest | LibraryFileCreate, request: Request, user: CurrentUserDep):
    if isinstance(payload, LibraryFileCreate):
        return ApiResponse(data=await library_service.create_file(payload))
    generated: GenerateFileResponse = await file_generation_service.generate_file(payload, get_frappe_cookies(request), user.user)
    return ApiResponse(data=generated).model_dump(mode="json", exclude_none=True)


@router.get("/files/{file_id}", response_model=ApiResponse[LibraryFile])
async def file_metadata(file_id: str, request: Request, user: CurrentUserDep) -> ApiResponse[LibraryFile]:
    return ApiResponse(data=await library_service.get_file_metadata(file_id, get_frappe_cookies(request), user.user, user.roles))


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, request: Request, user: CurrentUserDep) -> Response:
    content, mime_type, filename = await library_service.download_file(file_id, get_frappe_cookies(request), user.user, user.roles)
    return Response(content=content, media_type=mime_type, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}", "Cache-Control": "private, no-store"})


@router.delete("/files/{file_id}", response_model=ApiResponse[DeleteResult])
async def delete_file(file_id: str, request: Request, user: CurrentUserDep) -> ApiResponse[DeleteResult]:
    return ApiResponse(data=await library_service.delete_file(file_id, get_frappe_cookies(request), user.user, user.roles))
