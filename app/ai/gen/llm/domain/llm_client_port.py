from typing import Protocol

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage


class LLMClientPort(Protocol):
    async def generate_ai_response(self, user_messages: list[AIMessage]) -> AIAssistantResponse: ...
