from app.agents.runtime import AgentContext, AgentResult
class BIAgent:
    async def handle(self, context: AgentContext) -> AgentResult: return AgentResult(agent_name="bi_agent", content="Dashboard visualization prepared.")
