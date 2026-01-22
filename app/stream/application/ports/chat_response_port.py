from typing import Protocol


class ChatResponsePort(Protocol):
    async def generate_response(self, prompt: str, channel_name: str) -> str: ...
