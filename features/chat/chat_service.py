from datetime import datetime, timedelta
from sqlalchemy import func
from db.base import SessionLocal
from features.chat.db.chat_message import ChatMessage
from features.chat.chat_schemas import TopChatUser


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

    def get_top_chat_users(self, channel_name: str, days: int, limit: int) -> list[TopChatUser]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            user_stats = (
                db.query(ChatMessage.user_name, func.count(ChatMessage.id).label('message_count'))
                .filter(ChatMessage.channel_name == channel_name)
                .filter(ChatMessage.created_at >= since)
                .group_by(ChatMessage.user_name)
                .order_by(func.count(ChatMessage.id).desc())
                .limit(limit)
                .all()
            )

            return [TopChatUser(username=stat.user_name, message_count=stat.message_count) for stat in user_stats]
        finally:
            db.close()
