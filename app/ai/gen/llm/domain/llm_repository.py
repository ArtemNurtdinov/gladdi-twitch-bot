from abc import ABC, abstractmethod

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage
from app.ai.gen.llm.domain.model.assistant import AIAssistant


class LLMRepository(ABC):
    @abstractmethod
    async def generate_ai_response(self, assistant: AIAssistant, user_messages: list[AIMessage]) -> AIAssistantResponse: ...

    @abstractmethod
    async def get_assistant(self, channel_name: str) -> AIAssistant | None: ...

    @abstractmethod
    async def save_assistant(self, channel_name: str, assistant: AIAssistant) -> None: ...
