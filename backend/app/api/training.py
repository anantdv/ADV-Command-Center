from fastapi import APIRouter

from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.schemas.training import AssessmentSubmission, Course, DetailedTrainingResult, GenerateAssessmentRequest, GeneratedAssessment, TrainingCourse, TrainingCourseCreate, TrainingLesson, TrainingResult
from app.services.training_service import training_service

router=APIRouter(prefix="/training",tags=["Training"])


@router.get("/courses",response_model=ApiResponse[list[Course]])
async def courses(_:CurrentUserDep)->ApiResponse[list[Course]]: return ApiResponse(data=await training_service.list_courses())


@router.post("/courses",response_model=ApiResponse[TrainingCourse])
async def create_course(payload:TrainingCourseCreate,user:CurrentUserDep)->ApiResponse[TrainingCourse]: return ApiResponse(data=await training_service.create_course(payload,user.roles))


@router.get("/courses/{course_id}",response_model=ApiResponse[TrainingCourse])
async def get_course(course_id:str,_:CurrentUserDep)->ApiResponse[TrainingCourse]: return ApiResponse(data=await training_service.get_course(course_id))


@router.get("/courses/{course_id}/lessons",response_model=ApiResponse[list[TrainingLesson]])
async def lessons(course_id:str,_:CurrentUserDep)->ApiResponse[list[TrainingLesson]]: return ApiResponse(data=await training_service.list_lessons(course_id))


@router.post("/assessments/generate",response_model=ApiResponse[GeneratedAssessment])
async def generate(payload:GenerateAssessmentRequest,user:CurrentUserDep)->ApiResponse[GeneratedAssessment]: return ApiResponse(data=await training_service.generate_assessment(payload,user.user,user.roles))


@router.post("/assessments/{assessment_id}/submit",response_model=ApiResponse[TrainingResult|DetailedTrainingResult])
async def submit(assessment_id:str,payload:AssessmentSubmission,user:CurrentUserDep)->ApiResponse[TrainingResult|DetailedTrainingResult]: return ApiResponse(data=await training_service.submit(assessment_id,payload,user.user))


@router.get("/results",response_model=ApiResponse[list[TrainingResult|DetailedTrainingResult]])
async def results(_:CurrentUserDep)->ApiResponse[list[TrainingResult|DetailedTrainingResult]]: return ApiResponse(data=await training_service.list_results())


@router.get("/leaderboard",response_model=ApiResponse[list[dict]])
async def leaderboard(_:CurrentUserDep)->ApiResponse[list[dict]]: return ApiResponse(data=await training_service.leaderboard())
