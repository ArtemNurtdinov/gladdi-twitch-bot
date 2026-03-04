from app.ai.gen.prompt.application.models.system_prompt import SystemPromptDTO
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.ai.gen.prompt.prompt_service import DEFAULT_SYSTEM_PROMPT_FOR_GROUP


class GetSystemPromptUseCase:
    def __init__(self, system_prompt_repository: SystemPromptRepository):
        self._system_prompt_repository = system_prompt_repository

    def handle(self, channel_name: str) -> SystemPromptDTO:
        saved_prompt = self._system_prompt_repository.get_system_prompt(channel_name)
        prompt = saved_prompt.prompt if saved_prompt else DEFAULT_SYSTEM_PROMPT_FOR_GROUP
        return SystemPromptDTO(channel_name=channel_name, prompt=prompt)
