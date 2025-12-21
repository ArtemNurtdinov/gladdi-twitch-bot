from datetime import datetime
from typing import Protocol, Sequence, Tuple, TypeVar, Generic

from app.chat.domain.models import ChatMessage

DB = TypeVar("DB")


class ChatRepository(Protocol, Generic[DB]):

    def save(self, db: DB, message: ChatMessage) -> None:
        ...

    def list_between(self, db: DB, channel_name: str, start: datetime, end: datetime) -> Sequence[ChatMessage]:
        ...

    def list_last(self, db: DB, channel_name: str, limit: int) -> Sequence[ChatMessage]:
        ...

    def top_chat_users(self, db: DB, limit: int, date_from: datetime | None, date_to: datetime | None) -> Sequence[Tuple[str, str, int]]:
        ...

    def get_last_chat_messages_since(self, db: DB, channel_name: str, since: datetime) -> list[ChatMessage]:
        ...
