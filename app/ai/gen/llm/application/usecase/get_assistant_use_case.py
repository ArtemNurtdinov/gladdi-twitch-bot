from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.domain.model.assistant import AIAssistant


class GetAssistantUseCase:
    def __init__(self, llm_repository: LLMRepository):
        self._llm_repository = llm_repository

    async def get_assistant(self, channel_name: str) -> AIAssistant:
        assistant = await self._llm_repository.get_assistant(channel_name)
        if assistant is None:
            assistant = AIAssistant.GPT_OSS_120B
        return assistant
