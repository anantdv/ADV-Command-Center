from app.schemas.support import AiHelpRequest
from app.services.support_service import support_service


class SupportTools:
    async def answer(self,question:str,user:str,roles:list[str],module:str|None=None): return await support_service.ai_help(AiHelpRequest(message=question,module=module),user,roles)


SUPPORT_TOOL_NAMES=["answer_support_question","create_support_ticket"]
