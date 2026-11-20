from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.infrastructure.client.openai_chat_client import OpenAIChatClient


class LLMRepositoryImpl(LLMRepository):
    def __init__(self, chat_client: OpenAIChatClient):
        self._chat_client = chat_client

    async def generate_ai_response(self, user_messages: list[AIMessage]) -> AIAssistantResponse:
        return await self._chat_client.generate(user_messages)
