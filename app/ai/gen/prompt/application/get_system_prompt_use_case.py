from app.ai.gen.prompt.application.system_prompt_port import SystemPromptPort
from app.ai.gen.prompt.prompt_service import DEFAULT_SYSTEM_PROMPT_FOR_GROUP


class GetSystemPromptUseCase:
    def __init__(self, system_prompt_port: SystemPromptPort):
        self._port = system_prompt_port

    def handle(self, channel_name: str) -> str:
        content = self._port.get(channel_name)
        return content if content else DEFAULT_SYSTEM_PROMPT_FOR_GROUP
