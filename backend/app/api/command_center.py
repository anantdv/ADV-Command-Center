from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.entity_resolution import EntitySearchRequest, EntitySearchResponse
from app.services.entity_resolution_service import entity_resolution_service

router = APIRouter(prefix="/command-center", tags=["Command Center"])


@router.post("/entity-search", response_model=ApiResponse[EntitySearchResponse])
async def entity_search(payload: EntitySearchRequest, request: Request, _: CurrentUserDep) -> ApiResponse[EntitySearchResponse]:
    return ApiResponse(data=await entity_resolution_service.search(payload, get_frappe_cookies(request)))
