from typing import Protocol

from app.ai.domain.models import AIMessage


class LLMClient(Protocol):
    def generate_ai_response(self, user_messages: list[AIMessage]) -> str:
        ...





