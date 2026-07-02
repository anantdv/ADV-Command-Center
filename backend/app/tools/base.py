from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    risk_level: Literal["low", "medium", "high"]
    requires_confirmation: bool = False
    permission_required: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class BaseTool:
    definition: ToolDefinition

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # TODO: Bind concrete implementation through the registry.
        return {"status": "placeholder", "tool": self.definition.name, "input": payload}
