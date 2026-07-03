import asyncio
import hashlib
import re

from app.config import settings
from app.core.exceptions import AppError
from app.llm.privacy_gateway import assert_safe_knowledge_content


class EmbeddingService:
    """Embeds approved knowledge text only; never accepts ERP tool output."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.embedding_provider

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        return (await self.embed_texts([text], task_type))[0]

    async def embed_texts(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        for text in texts:
            assert_safe_knowledge_content(text)
        if settings.use_mock_data or self.provider == "local_test":
            return [self._local_embedding(text) for text in texts]
        if self.provider != "vertex":
            raise AppError("Unsupported embedding provider.", 500)
        try:
            return await asyncio.to_thread(self._vertex_embeddings, texts, task_type)
        except AppError:
            raise
        except Exception as exc:
            raise AppError("Vertex embedding service is unavailable.", 502) from exc

    @staticmethod
    def _local_embedding(text: str, dimensions: int = 256) -> list[float]:
        vector = [0.0] * dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            vector[index] += 1.0
        norm = sum(value * value for value in vector) ** .5 or 1.0
        return [value / norm for value in vector]

    @staticmethod
    def _vertex_embeddings(texts: list[str], task_type: str) -> list[list[float]]:
        from google import genai
        from google.genai import types
        client = genai.Client(vertexai=True, project=settings.google_cloud_project, location=settings.google_cloud_location)
        output: list[list[float]] = []
        for start in range(0, len(texts), 20):
            batch = texts[start:start + 20]
            response = client.models.embed_content(
                model=settings.vertex_embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            embeddings = response.embeddings or []
            if len(embeddings) != len(batch):
                raise AppError("Vertex returned an incomplete embedding response.", 502)
            output.extend(list(item.values or []) for item in embeddings)
        return output
