from typing import Protocol

from app.ai.gen.domain.models import AIMessage


class LLMClient(Protocol):
    async def generate_ai_response(self, user_messages: list[AIMessage]) -> str: ...
