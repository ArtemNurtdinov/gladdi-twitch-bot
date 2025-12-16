from datetime import datetime
from typing import Optional

from sqlalchemy import func
from db.base import SessionLocal
from features.chat.db.chat_message import ChatMessage
from features.chat.chat_schemas import TopChatUser, TopChatUsersResponse


class ChatService:

    def save_chat_message(self, channel_name: str, user_name: str, content: str):
        db = SessionLocal()
        try:
            normalized_user = user_name.lower()
            msg = ChatMessage(channel_name=channel_name, user_name=normalized_user, content=content, created_at=datetime.utcnow())
            db.add(msg)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()

    def get_chat_messages(self, channel_name: str, from_time: datetime):
        db = SessionLocal()
        try:
            return db.query(ChatMessage).filter(ChatMessage.channel_name == channel_name).filter(ChatMessage.created_at >= from_time).all()
        finally:
            db.close()

    def get_chat_messages(self, channel_name: str, from_time, to_time) -> list[ChatMessage]:
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessage)
                .filter(ChatMessage.channel_name == channel_name)
                .filter(ChatMessage.created_at >= from_time)
                .filter(ChatMessage.created_at < to_time)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            return messages
        finally:
            db.close()

    def get_last_chat_messages(self, channel_name: str, limit: int):
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessage)
                .filter(ChatMessage.channel_name == channel_name)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
                .all()
            )
            messages.reverse()
            return messages
        finally:
            db.close()

    def get_top_chat_users(self, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> TopChatUsersResponse:
        db = SessionLocal()
        try:
            query = db.query(ChatMessage.channel_name, ChatMessage.user_name, func.count(ChatMessage.id).label('message_count'))

            if date_from:
                query = query.filter(ChatMessage.created_at >= date_from)
            if date_to:
                query = query.filter(ChatMessage.created_at <= date_to)

            query = query.group_by(ChatMessage.channel_name, ChatMessage.user_name).order_by(func.count(ChatMessage.id).desc()).limit(limit)
            user_stats = query.all()
            users = [TopChatUser(channel_name=stat.channel_name, username=stat.user_name, message_count=stat.message_count) for stat in user_stats]
            return TopChatUsersResponse(top_users=users)
        finally:
            db.close()
