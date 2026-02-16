from app.ai.gen.prompt.application.system_prompt_port import SystemPromptPort


class UpdateSystemPromptUseCase:
    def __init__(self, system_prompt_port: SystemPromptPort):
        self._port = system_prompt_port

    def handle(self, channel_name: str, content: str) -> None:
        self._port.set(channel_name, content)
