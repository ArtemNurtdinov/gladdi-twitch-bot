from typing import Protocol


class GenerateStreamInfoPort(Protocol):
    async def generate(self, prompt: str, channel_name: str) -> str: ...
