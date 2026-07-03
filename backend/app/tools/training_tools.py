from app.schemas.training import GenerateAssessmentRequest
from app.services.training_service import training_service


class TrainingTools:
    async def generate_assessment(self,source_id:str,user:str,roles:list[str],question_count:int=5): return await training_service.generate_assessment(GenerateAssessmentRequest(source_id=source_id,question_count=question_count),user,roles)


TRAINING_TOOL_NAMES=["generate_training_assessment"]
