from app.ai.gen.prompt.domain.models.system_prompt import SystemPrompt


class SystemPromptRepository:
    def get_system_prompt(self, channel_name: str) -> SystemPrompt | None: ...

    def save_system_prompt(self, system_prompt: SystemPrompt) -> None: ...
