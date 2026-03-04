from app.ai.gen.prompt.domain.models.system_prompt import SystemPrompt
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository


class UpdateSystemPromptUseCase:
    def __init__(self, system_prompt_repository: SystemPromptRepository):
        self._system_prompt_repository = system_prompt_repository

    def update_system_prompt(self, channel_name: str, content: str) -> None:
        system_prompt = SystemPrompt(channel_name, content)
        self._system_prompt_repository.save_system_prompt(system_prompt)
