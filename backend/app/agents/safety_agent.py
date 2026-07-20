from pydantic import BaseModel

from app.agents.router_agent import IntentResult, RouterAgent
from app.agents.runtime import AgentContext, AgentResult


class SafetyResult(BaseModel):
    allowed: bool
    reason: str | None = None
    sensitive_intent: bool = False
    risk_level: str = "low"


class SafetyAgent:
    async def validate(self, intent: IntentResult) -> SafetyResult:
        text = intent.raw_prompt.lower()
        if intent.intent.startswith("workflow_"):
            return SafetyResult(allowed=True, sensitive_intent=False, risk_level="medium" if intent.intent == "workflow_apply_action" else "low")
        if intent.intent in {"crud_create", "crud_update"}:
            return SafetyResult(allowed=True, sensitive_intent=False, risk_level="medium")
        if intent.intent == "blocked_write" or intent.write_requested or RouterAgent._blocked_write_requested(" ".join(text.split())):
            return SafetyResult(
                allowed=False,
                reason="This action is not enabled yet. I can prepare a draft or show related records, but I cannot submit, cancel, delete, create payments, create journal entries, or perform bulk updates in this stage.",
                risk_level="high",
            )
        if any(term in text for term in ("password", "api key", "api keys", "api secret", "token", "otp")):
            return SafetyResult(allowed=False, reason="Credential and secret fields cannot be queried through Command Center.", risk_level="high")
        if any(term in text for term in ("ignore permission", "bypass permission", "use admin", "administrator access")):
            return SafetyResult(allowed=False, reason="I cannot bypass ERPNext permissions or use elevated access.", risk_level="high")
        if any(term in text for term in ("run sql", "raw sql", "sql query", "dump customer table", "dump table")):
            return SafetyResult(allowed=False, reason="Direct SQL and database dumps are not available. I can use ERPNext reports and records.", risk_level="high")
        if any(term in text for term in ("salary", "salaries", "payroll")):
            return SafetyResult(allowed=False, reason="Salary and payroll queries require a dedicated sensitive-data workflow and are disabled here.", sensitive_intent=True, risk_level="high")
        return SafetyResult(allowed=True, sensitive_intent=intent.sensitive_intent, risk_level="low")

    async def handle(self, context: AgentContext) -> AgentResult:
        # Compatibility method for the future generic AgentRuntime.
        return AgentResult(agent_name="safety_agent", content="Use validate(IntentResult) for read-only safety checks.")
