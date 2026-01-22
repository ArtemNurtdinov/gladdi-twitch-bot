from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.stream.application.ports.chat_response_port import ChatResponsePort


class ChatResponseAdapter(ChatResponsePort):
    def __init__(self, use_case: ChatResponseUseCase):
        self._use_case = use_case

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        return await self._use_case.generate_response(prompt, channel_name)
