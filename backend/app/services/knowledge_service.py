import asyncio
import hashlib
import json
from pathlib import Path

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.schemas.knowledge import KnowledgeChunk, KnowledgeSearchRequest, KnowledgeSearchResult, KnowledgeSource, KnowledgeSourceCreateRequest
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.text_chunker import chunk_text

APPROVER_ROLES = {"System Manager", "AI Training Manager", "Training Manager", "AI Command Center Manager"}


class KnowledgeService:
    """Private approved-source registry and ingestion boundary."""

    def __init__(self, root: str | None = None, embeddings: EmbeddingService | None = None, vectors: VectorStoreService | None = None):
        self.root = Path(root or settings.knowledge_storage_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.sources_path = self.root / "sources.json"
        self.ingestion = DocumentIngestionService(str(self.root))
        self.embeddings = embeddings or EmbeddingService()
        self.vectors = vectors or VectorStoreService(str(self.root))
        self._lock = asyncio.Lock()

    async def create_source(self, request: KnowledgeSourceCreateRequest, user: str) -> KnowledgeSource:
        source_id = new_id("src")
        now = utc_now().isoformat()
        record = {
            "source_id":source_id,"title":request.title,"source_type":request.source_type,
            "module":request.module,"description":request.description,"status":"draft",
            "allowed_roles":list(dict.fromkeys(request.allowed_roles)),
            "allowed_modules":list(dict.fromkeys(request.allowed_modules)),
            "file_id":request.file_id,"created_by":user,"created_at":now,"updated_at":now,
        }
        if request.content:
            record["content_path"] = self.ingestion.save_inline_content(source_id, request.content)
        async with self._lock:
            records = self._load_records(); records.append(record); self._save_records(records)
        await self._audit("knowledge_source_created", user, record)
        return self._public(record)

    async def approve_source(self, source_id: str, user: str, user_roles: list[str] | None = None) -> KnowledgeSource:
        if not APPROVER_ROLES.intersection(user_roles or []):
            raise PermissionDenied("Only a Training Manager or System Manager can approve knowledge sources.")
        async with self._lock:
            records = self._load_records(); record = self._find(records, source_id)
            record["status"] = "approved"; record["updated_at"] = utc_now().isoformat(); self._save_records(records)
        await self._audit("knowledge_source_approved", user, record)
        return self._public(record)

    async def ingest_source(self, source_id: str, user: str, user_roles: list[str] | None = None) -> dict:
        if not APPROVER_ROLES.intersection(user_roles or []):
            raise PermissionDenied("Only a Training Manager or System Manager can ingest knowledge sources.")
        record = self._find(self._load_records(), source_id)
        if record["status"] != "approved":
            raise AppError("Only approved knowledge sources can be ingested.", 409)
        text = self.ingestion.get_source_text(record)
        pieces = chunk_text(text, settings.knowledge_chunk_size, settings.knowledge_chunk_overlap)
        if not pieces:
            raise AppError("No knowledge chunks could be created.", 422)
        chunks = [KnowledgeChunk(chunk_id=new_id("chunk"),source_id=source_id,chunk_index=index,title=record["title"],content=piece,module=record.get("module"),source_type=record["source_type"],citation_label=f"{record['title']} · section {index+1}",allowed_roles=record.get("allowed_roles",[]),metadata={"status":"approved","allowed_modules":record.get("allowed_modules",[])}) for index,piece in enumerate(pieces)]
        embeddings = await self.embeddings.embed_texts(pieces)
        await self.vectors.add_chunks(chunks, embeddings)
        await self._audit("knowledge_source_ingested", user, record, top_k=len(chunks))
        return {"source_id":source_id,"chunk_count":len(chunks),"indexed":True}

    async def search(self, request: KnowledgeSearchRequest, user: str, user_roles: list[str]) -> list[KnowledgeSearchResult]:
        embedding = await self.embeddings.embed_text(request.query, "RETRIEVAL_QUERY")
        results = await self.vectors.search(embedding, request.top_k, request.module, user_roles)
        await log_audit_event(AuditEvent(user=user,action="knowledge_search_performed",agent_name="knowledge_service",allowed=True,risk_level="low",module=request.module,query_hash=self.query_hash(request.query),citation_ids=[item.chunk_id for item in results],top_k=request.top_k,record_count=len(results),erp_data_sent=False))
        return results

    async def list_sources(self, status: str | None = None, user_roles: list[str] | None = None) -> list[KnowledgeSource]:
        roles = set(user_roles or [])
        records = self._load_records()
        return [self._public(record) for record in records if (not status or record["status"] == status) and (not record.get("allowed_roles") or roles.intersection(record["allowed_roles"]) or "System Manager" in roles)]

    async def get_source(self, source_id: str, user_roles: list[str] | None = None) -> KnowledgeSource:
        record = self._find(self._load_records(), source_id)
        roles = set(user_roles or [])
        if record.get("allowed_roles") and not roles.intersection(record["allowed_roles"]) and "System Manager" not in roles:
            raise PermissionDenied("You do not have access to this knowledge source.")
        return self._public(record)

    def chunks_for_source(self, source_id: str, user_roles: list[str]) -> list[KnowledgeChunk]:
        source = self._find(self._load_records(), source_id)
        if source["status"] != "approved":
            raise AppError("Assessment source must be approved.", 409)
        roles = set(user_roles)
        if source.get("allowed_roles") and not roles.intersection(source["allowed_roles"]) and "System Manager" not in roles:
            raise PermissionDenied("You do not have access to this training source.")
        return self.vectors.chunks_for_source(source_id)

    @staticmethod
    def query_hash(query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]

    def _load_records(self) -> list[dict]:
        if not self.sources_path.exists(): return []
        try: return json.loads(self.sources_path.read_text(encoding="utf-8"))
        except (ValueError, OSError): return []

    def _save_records(self, records: list[dict]) -> None:
        temporary = self.sources_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
        temporary.replace(self.sources_path)

    @staticmethod
    def _find(records: list[dict], source_id: str) -> dict:
        record = next((item for item in records if item.get("source_id") == source_id), None)
        if not record: raise AppError("Knowledge source not found.", 404)
        return record

    @staticmethod
    def _public(record: dict) -> KnowledgeSource:
        return KnowledgeSource.model_validate({key:value for key,value in record.items() if key != "content_path"})

    @staticmethod
    async def _audit(action: str, user: str, record: dict, top_k: int | None = None) -> None:
        await log_audit_event(AuditEvent(user=user,action=action,agent_name="knowledge_service",allowed=True,risk_level="low",source_id=record["source_id"],source_type=record["source_type"],module=record.get("module"),top_k=top_k,erp_data_sent=False))


knowledge_service = KnowledgeService()
