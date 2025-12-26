from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.chat.domain.models import ChatMessage, TopChatUserInfo
from app.chat.domain.repo import ChatRepository


class ChatUseCase:

    def __init__(self, repo: ChatRepository):
        self._repo = repo

    def save_chat_message(self, channel_name: str, user_name: str, content: str, current_time: datetime) -> None:
        normalized_channel = channel_name.strip()
        normalized_user = user_name.strip()
        normalized_content = content.strip()

        if not normalized_channel:
            raise ValueError("channel_name must be provided")
        if not normalized_user:
            raise ValueError("user_name must be provided")
        if not normalized_content:
            raise ValueError("content must be non-empty")

        message = ChatMessage(
            channel_name=normalized_channel,
            user_name=normalized_user,
            content=normalized_content,
            created_at=current_time,
        )
        self._repo.save(message)

    def get_chat_messages(self, channel_name: str, from_time: datetime, to_time: datetime) -> list[ChatMessage]:
        if from_time > to_time:
            raise ValueError("from_time must be earlier or equal to to_time")
        return list(self._repo.list_between(channel_name, from_time, to_time))

    def get_last_chat_messages(self, channel_name: str, limit: int) -> list[ChatMessage]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return list(self._repo.list_last(channel_name, limit))

    def get_top_chat_users(self, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> list[TopChatUserInfo]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be greater than date_to")
        stats = self._repo.top_chat_users(limit, date_from, date_to)
        return [TopChatUserInfo(channel_name=channel, username=user, message_count=count) for channel, user, count in stats]

    def get_last_chat_messages_since(self, channel_name: str, since: datetime) -> list[ChatMessage]:
        return self._repo.get_last_chat_messages_since(channel_name, since)





