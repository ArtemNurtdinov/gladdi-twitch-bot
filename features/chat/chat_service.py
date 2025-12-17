from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from features.chat.db.chat_message import ChatMessage
from features.chat.chat_schemas import TopChatUser, TopChatUsersResponse


class ChatService:

    def save_chat_message(self, db: Session, channel_name: str, user_name: str, content: str):
        msg = ChatMessage(channel_name=channel_name, user_name=user_name, content=content, created_at=datetime.utcnow())
        db.add(msg)

    def get_chat_messages(self, db: Session, channel_name: str, from_time: datetime, to_time: datetime) -> list[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.channel_name == channel_name)
            .filter(ChatMessage.created_at >= from_time)
            .filter(ChatMessage.created_at < to_time)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def get_last_chat_messages(self, db: Session, channel_name: str, limit: int) -> list[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.channel_name == channel_name)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()[::-1]
        )

    def get_top_chat_users(self, db: Session, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> TopChatUsersResponse:
        count_expr = func.count(ChatMessage.id).label("message_count")
        query = db.query(ChatMessage.channel_name, ChatMessage.user_name, count_expr)
        if date_from:
            query = query.filter(ChatMessage.created_at >= date_from)
        if date_to:
            query = query.filter(ChatMessage.created_at <= date_to)

        query = query.group_by(ChatMessage.channel_name, ChatMessage.user_name).order_by(count_expr.desc()).limit(limit)
        user_stats = query.all()
        users = [TopChatUser(channel_name=stat.channel_name, username=stat.user_name, message_count=stat.message_count) for stat in user_stats]
        return TopChatUsersResponse(top_users=users)
