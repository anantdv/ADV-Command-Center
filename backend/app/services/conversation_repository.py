from typing import Any

from app.schemas.chat import ChatMessage, Conversation
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class InMemoryConversationRepository:
    """Persistence boundary used until SQLAlchemy repositories are enabled."""

    def __init__(self) -> None:
        now = utc_now()
        initial = Conversation(
            id="conv-welcome",
            title="Welcome — ask Tinni about your ERP",
            created_at=now,
            updated_at=now,
        )
        self.conversations: dict[str, Conversation] = {initial.id: initial}
        self.messages: dict[str, list[ChatMessage]] = {initial.id: []}
        self.tool_calls: list[dict[str, Any]] = []
        self.result_contexts: dict[str, list[dict[str, Any]]] = {}

    async def list_conversations(self) -> list[Conversation]:
        return sorted(self.conversations.values(), key=lambda item: item.updated_at, reverse=True)

    async def create_conversation(self, title: str, conversation_id: str | None = None) -> Conversation:
        now = utc_now()
        conversation = Conversation(
            id=conversation_id or new_id("conv"),
            title=title,
            created_at=now,
            updated_at=now,
        )
        self.conversations[conversation.id] = conversation
        self.messages.setdefault(conversation.id, [])
        return conversation

    async def get_or_create(self, conversation_id: str | None, title: str) -> Conversation:
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        return await self.create_conversation(title, conversation_id)

    async def get_messages(self, conversation_id: str) -> list[ChatMessage]:
        return self.messages.get(conversation_id, [])

    async def save_message(self, message: ChatMessage) -> None:
        self.messages.setdefault(message.conversation_id, []).append(message)
        conversation = self.conversations.get(message.conversation_id)
        if conversation:
            self.conversations[message.conversation_id] = conversation.model_copy(
                update={"updated_at": message.created_at}
            )
        # TODO: Replace with an AIMessage SQLAlchemy repository transaction.

    async def save_tool_call(self, tool_call: dict[str, Any]) -> None:
        self.tool_calls.append(tool_call)
        # TODO: Replace with an AIToolCall SQLAlchemy repository transaction.

    async def save_result_context(self, conversation_id: str, context: dict[str, Any]) -> None:
        self.result_contexts.setdefault(conversation_id, []).append(context)
        # TODO: Replace with an AIReportResult SQLAlchemy repository transaction.

    async def get_latest_result_context(self, conversation_id: str) -> dict[str, Any] | None:
        contexts = self.result_contexts.get(conversation_id) or []
        return contexts[-1] if contexts else None

    async def get_result_context(
        self,
        conversation_id: str,
        result_id: str | None = None,
        report_id: str | None = None,
    ) -> dict[str, Any] | None:
        contexts = self.result_contexts.get(conversation_id) or []
        if not result_id and not report_id:
            return contexts[-1] if contexts else None
        for context in reversed(contexts):
            if result_id and context.get("result_id") == result_id:
                return context
            if report_id and context.get("report_id") == report_id:
                return context
        return None
