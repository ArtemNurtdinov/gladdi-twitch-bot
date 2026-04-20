from abc import ABC, abstractmethod

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage


class LLMRepository(ABC):
    @abstractmethod
    async def generate_ai_response(self, channel_name: str, user_messages: list[AIMessage]) -> AIAssistantResponse: ...
