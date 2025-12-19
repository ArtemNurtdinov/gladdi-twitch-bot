from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from features.chat.domain.models import ChatMessage as DomainChatMessage, TopChatUserInfo
from features.chat.domain.repo import ChatRepository


class ChatService:

    def __init__(self, repo: ChatRepository[Session]):
        self._repo = repo

    def save_chat_message(self, db: Session, channel_name: str, user_name: str, content: str):
        self._repo.save(db, DomainChatMessage(channel_name=channel_name, user_name=user_name, content=content, created_at=datetime.utcnow()))

    def get_chat_messages(self, db: Session, channel_name: str, from_time: datetime, to_time: datetime) -> list[DomainChatMessage]:
        return list(self._repo.list_between(db, channel_name, from_time, to_time))

    def get_last_chat_messages(self, db: Session, channel_name: str, limit: int) -> list[DomainChatMessage]:
        return list(self._repo.list_last(db, channel_name, limit))

    def get_top_chat_users(self, db: Session, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> list[TopChatUserInfo]:
        stats = self._repo.top_chat_users(db, limit, date_from, date_to)
        return [TopChatUserInfo(channel_name=channel, username=user, message_count=count) for channel, user, count in stats]

    def get_last_chat_messages_since(self, db: Session, channel_name: str, since: datetime) -> list[DomainChatMessage]:
        return self._repo.get_last_chat_messages_since(db, channel_name, since)
