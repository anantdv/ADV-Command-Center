from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.router_agent import RouterAgent
from app.config import settings
from app.core.exceptions import AppError
from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse

router=APIRouter(prefix="/debug",tags=["Development"])


class ExtractIntentRequest(BaseModel):
    message: str = Field(min_length=1,max_length=8000)
    module_context: str | None = None


@router.post("/extract-intent", response_model=ApiResponse[dict])
async def extract_intent(payload: ExtractIntentRequest, _: CurrentUserDep) -> ApiResponse[dict]:
    if settings.app_env != "development": raise AppError("Not found.",404)
    intent=await RouterAgent().classify(payload.message,payload.module_context)
    safe=intent.model_dump(exclude={"raw_prompt","rows","chart_config"},mode="json")
    return ApiResponse(data={"extraction_method":intent.extraction_method,"intent":safe,"raw_model_output":None})
