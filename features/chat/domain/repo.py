from datetime import datetime
from typing import Protocol, Sequence, Tuple, TypeVar, Generic

from features.chat.domain.models import ChatMessage

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
