from typing import Protocol

from app.ai.domain.models import AIMessage


class AIMessageRepository(Protocol):
    def get_last_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        ...

    def add_messages_to_db(self, channel_name: str, user_message: str, ai_message: str) -> None:
        ...


