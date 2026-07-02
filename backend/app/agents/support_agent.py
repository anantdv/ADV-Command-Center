from app.agents.runtime import AgentContext, AgentResult
class SupportAgent:
    async def handle(self, context: AgentContext) -> AgentResult: return AgentResult(agent_name="support_agent", content="Support diagnosis prepared.")
