from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    raw: dict[str, Any] | None = None
    model: str | None = None
    provider: str | None = None
    latency_ms: int | None = None


class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[LLMMessage], response_schema: dict[str, Any] | None = None, **kwargs) -> LLMResponse:
        """Return model text without executing tools or accessing ERPNext."""

