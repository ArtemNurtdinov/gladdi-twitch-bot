from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage
from app.ai.gen.llm.domain.llm_repository import LLMRepository


class GenerateAIResponseUseCase:
    def __init__(self, llm_repository: LLMRepository):
        self._llm_repository = llm_repository

    async def generate_ai_response(self, user_messages: list[AIMessage]) -> AIAssistantResponse:
        return await self._llm_repository.generate_ai_response(user_messages)
