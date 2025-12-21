from datetime import datetime
from typing import Optional

from app.chat.domain.models import ChatMessage as DomainChatMessage, TopChatUserInfo
from app.chat.domain.repo import ChatRepository


class ChatService:
    def __init__(self, repo: ChatRepository):
        self._repo = repo

    def save_chat_message(self, channel_name: str, user_name: str, content: str):
        self._repo.save(DomainChatMessage(channel_name=channel_name, user_name=user_name, content=content, created_at=datetime.utcnow()))

    def get_chat_messages(self, channel_name: str, from_time: datetime, to_time: datetime) -> list[DomainChatMessage]:
        return list(self._repo.list_between(channel_name, from_time, to_time))

    def get_last_chat_messages(self, channel_name: str, limit: int) -> list[DomainChatMessage]:
        return list(self._repo.list_last(channel_name, limit))

    def get_top_chat_users(self, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> list[TopChatUserInfo]:
        stats = self._repo.top_chat_users(limit, date_from, date_to)
        return [TopChatUserInfo(channel_name=channel, username=user, message_count=count) for channel, user, count in stats]

    def get_last_chat_messages_since(self, channel_name: str, since: datetime) -> list[DomainChatMessage]:
        return self._repo.get_last_chat_messages_since(channel_name, since)
