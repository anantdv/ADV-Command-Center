from app.schemas.knowledge import KnowledgeSearchRequest, RAGAnswerRequest
from app.services.knowledge_service import knowledge_service
from app.services.rag_service import rag_service


class KnowledgeTools:
    async def search(self,query:str,user:str,roles:list[str],module:str|None=None): return await knowledge_service.search(KnowledgeSearchRequest(query=query,module=module),user,roles)
    async def answer(self,question:str,user:str,roles:list[str],module:str|None=None): return await rag_service.answer_question(RAGAnswerRequest(question=question,module=module),user,roles)
