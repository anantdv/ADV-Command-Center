from app.agents.runtime import AgentContext, AgentResult
class TrainingAgent:
    async def handle(self, context: AgentContext) -> AgentResult: return AgentResult(agent_name="training_agent", content="Training recommendation prepared.")
