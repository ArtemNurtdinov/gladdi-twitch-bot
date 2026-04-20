from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.domain.model.assistant import AIAssistant


class SaveAssistantUseCase:
    def __init__(self, llm_repository: LLMRepository):
        self._llm_repository = llm_repository

    async def save_assistant(self, channel_name: str, assistant: AIAssistant) -> None:
        await self._llm_repository.save_assistant(channel_name, assistant)
