from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import Intent


class AgentContext(BaseModel):
    user: str
    message: str
    conversation_id: str | None = None
    intent: Intent = Intent.GENERAL_QUESTION
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    success: bool = True
    content: str
    data: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class AgentRuntime:
    """Future orchestration loop for routing, tools, safety, and streaming."""

    async def execute(self, context: AgentContext) -> AgentResult:
        # TODO: Add iterative tool execution and SSE event emission.
        return AgentResult(agent_name="runtime", content=f"Intent {context.intent} accepted for orchestration.")
