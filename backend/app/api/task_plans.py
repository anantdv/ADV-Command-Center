from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.schemas.task_plan import ExecutionPlan
from app.services.chat_service import chat_service

router = APIRouter(prefix="/task-plans", tags=["Task Plans"])


@router.get("/conversation/{conversation_id}", response_model=ApiResponse[list[ExecutionPlan]])
async def list_conversation_plans(conversation_id: str, _: CurrentUserDep) -> ApiResponse[list[ExecutionPlan]]:
    return ApiResponse(data=await chat_service.get_plans(conversation_id))


@router.get("/{plan_id}", response_model=ApiResponse[ExecutionPlan])
async def get_plan(plan_id: str, _: CurrentUserDep) -> ApiResponse[ExecutionPlan]:
    plan = await chat_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found.")
    return ApiResponse(data=plan)


@router.post("/{plan_id}/cancel", response_model=ApiResponse[ExecutionPlan])
async def cancel_plan(plan_id: str, user: CurrentUserDep) -> ApiResponse[ExecutionPlan]:
    plan = await chat_service.cancel_plan(plan_id, user.user)
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found.")
    return ApiResponse(data=plan, message="Execution plan cancelled.")


@router.post("/{plan_id}/retry", response_model=ApiResponse[ExecutionPlan])
async def retry_plan(plan_id: str, user: CurrentUserDep) -> ApiResponse[ExecutionPlan]:
    plan = await chat_service.retry_plan(plan_id, user.user)
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found.")
    return ApiResponse(data=plan, message="Execution plan retry requested.")

