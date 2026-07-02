from fastapi import APIRouter

from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.schemas.training import AssessmentSubmission, Course, TrainingResult
from app.services.training_service import training_service

router = APIRouter(prefix="/training", tags=["Training"])


@router.get("/courses", response_model=ApiResponse[list[Course]])
async def courses(_: CurrentUserDep) -> ApiResponse[list[Course]]: return ApiResponse(data=await training_service.list_courses())


@router.get("/results", response_model=ApiResponse[list[TrainingResult]])
async def results(_: CurrentUserDep) -> ApiResponse[list[TrainingResult]]: return ApiResponse(data=await training_service.list_results())


@router.post("/assessments/{assessment_id}/submit", response_model=ApiResponse[TrainingResult])
async def submit(assessment_id: str, payload: AssessmentSubmission, _: CurrentUserDep) -> ApiResponse[TrainingResult]: return ApiResponse(data=await training_service.submit(assessment_id, payload))
