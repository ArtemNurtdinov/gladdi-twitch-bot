from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from app.chat.domain.models import ChatMessage


class ChatRepository(Protocol):
    def save(self, message: ChatMessage) -> None: ...

    def list_between(self, channel_name: str, start: datetime, end: datetime) -> Sequence[ChatMessage]: ...

    def list_last(self, channel_name: str, limit: int) -> Sequence[ChatMessage]: ...

    def top_chat_users(self, limit: int, date_from: datetime | None, date_to: datetime | None) -> Sequence[tuple[str, str, int]]: ...

    def get_last_chat_messages_since(self, channel_name: str, since: datetime) -> list[ChatMessage]: ...
