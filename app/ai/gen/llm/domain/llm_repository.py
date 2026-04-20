from abc import ABC, abstractmethod

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage
from app.ai.gen.llm.domain.model.assistant import AIAssistant


class LLMRepository(ABC):
    @abstractmethod
    async def generate_ai_response(self, user_messages: list[AIMessage], assistant: AIAssistant) -> AIAssistantResponse: ...
