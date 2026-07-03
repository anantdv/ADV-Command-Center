import asyncio
import json
from pathlib import Path

import numpy as np

from app.config import settings
from app.schemas.knowledge import KnowledgeChunk, KnowledgeSearchResult


class VectorStoreService:
    """Small private vector index using JSONL metadata and NumPy cosine search."""

    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.knowledge_storage_root).resolve() / "vector_store"
        self.root.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.root / "chunks.jsonl"
        self.embeddings_path = self.root / "embeddings.npy"
        self.meta_path = self.root / "index_meta.json"
        self._lock = asyncio.Lock()

    async def add_chunks(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length")
        async with self._lock:
            current_chunks, current_embeddings = self._load()
            source_ids = {chunk.source_id for chunk in chunks}
            keep = [index for index, chunk in enumerate(current_chunks) if chunk.source_id not in source_ids]
            kept_chunks = [current_chunks[index] for index in keep]
            if keep and current_embeddings.size:
                kept_embeddings = current_embeddings[keep]
            else:
                dimension = len(embeddings[0]) if embeddings else (current_embeddings.shape[1] if current_embeddings.ndim == 2 and current_embeddings.size else 0)
                kept_embeddings = np.empty((0, dimension), dtype=np.float32)
            new_embeddings = np.asarray(embeddings, dtype=np.float32)
            combined = np.vstack([kept_embeddings, new_embeddings]) if kept_embeddings.size and new_embeddings.size else (new_embeddings if new_embeddings.size else kept_embeddings)
            self._write([*kept_chunks, *chunks], combined)

    async def search(self, query_embedding: list[float], top_k: int = 5, module: str | None = None, user_roles: list[str] | None = None) -> list[KnowledgeSearchResult]:
        chunks, embeddings = self._load()
        if not chunks or not embeddings.size:
            return []
        query = np.asarray(query_embedding, dtype=np.float32)
        if embeddings.shape[1] != query.shape[0]:
            return []
        roles = set(user_roles or [])
        allowed_indices = []
        for index, chunk in enumerate(chunks):
            status = chunk.metadata.get("status")
            role_allowed = not chunk.allowed_roles or bool(roles.intersection(chunk.allowed_roles)) or "System Manager" in roles
            module_allowed = not module or not chunk.module or chunk.module.lower() == module.lower()
            allowed_modules = [str(item).lower() for item in chunk.metadata.get("allowed_modules", [])]
            if allowed_modules and (not module or module.lower() not in allowed_modules):
                module_allowed = False
            if status == "approved" and role_allowed and module_allowed:
                allowed_indices.append(index)
        if not allowed_indices:
            return []
        matrix = embeddings[allowed_indices]
        norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(query) or 1.0)
        scores = np.divide(matrix @ query, norms, out=np.zeros_like(norms), where=norms != 0)
        ranked = sorted(zip(allowed_indices, scores.tolist()), key=lambda item: item[1], reverse=True)[:min(top_k, 20)]
        return [KnowledgeSearchResult(chunk_id=chunks[index].chunk_id,source_id=chunks[index].source_id,title=chunks[index].title,snippet=chunks[index].content[:500],score=round(float(score),6),citation_label=chunks[index].citation_label,source_type=chunks[index].source_type,module=chunks[index].module) for index, score in ranked if score > 0]

    def chunks_for_source(self, source_id: str) -> list[KnowledgeChunk]:
        return [chunk for chunk in self._load()[0] if chunk.source_id == source_id and chunk.metadata.get("status") == "approved"]

    def _load(self) -> tuple[list[KnowledgeChunk], np.ndarray]:
        chunks: list[KnowledgeChunk] = []
        if self.chunks_path.exists():
            for line in self.chunks_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    chunks.append(KnowledgeChunk.model_validate_json(line))
        if self.embeddings_path.exists():
            with self.embeddings_path.open("rb") as handle:
                embeddings = np.load(handle, allow_pickle=False)
        else:
            embeddings = np.empty((0, 0), dtype=np.float32)
        if len(chunks) != len(embeddings):
            return [], np.empty((0, 0), dtype=np.float32)
        return chunks, embeddings

    def _write(self, chunks: list[KnowledgeChunk], embeddings: np.ndarray) -> None:
        chunks_tmp = self.chunks_path.with_suffix(".tmp")
        embeddings_tmp = self.embeddings_path.with_suffix(".tmp")
        chunks_tmp.write_text("\n".join(chunk.model_dump_json() for chunk in chunks) + ("\n" if chunks else ""), encoding="utf-8")
        with embeddings_tmp.open("wb") as handle:
            np.save(handle, embeddings, allow_pickle=False)
        chunks_tmp.replace(self.chunks_path)
        embeddings_tmp.replace(self.embeddings_path)
        self.meta_path.write_text(json.dumps({"count":len(chunks),"dimensions":int(embeddings.shape[1]) if embeddings.ndim == 2 and embeddings.size else 0}), encoding="utf-8")
