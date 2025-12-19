from datetime import datetime
from typing import Sequence, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from features.chat.domain.models import ChatMessage
from features.chat.domain.repo import ChatRepository
from features.chat.data.db.chat_message import ChatMessage as ChatMessageORM


class ChatRepositoryImpl(ChatRepository[Session]):

    def save(self, db: Session, message: ChatMessage) -> None:
        db.add(ChatMessageORM(channel_name=message.channel_name, user_name=message.user_name, content=message.content, created_at=message.created_at))

    def list_between(self, db: Session, channel_name: str, start: datetime, end: datetime) -> Sequence[ChatMessage]:
        rows = (
            db.query(ChatMessageORM)
            .filter(ChatMessageORM.channel_name == channel_name)
            .filter(ChatMessageORM.created_at >= start)
            .filter(ChatMessageORM.created_at < end)
            .order_by(ChatMessageORM.created_at.asc())
            .all()
        )
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in rows]

    def list_last(self, db: Session, channel_name: str, limit: int) -> Sequence[ChatMessage]:
        rows = (
            db.query(ChatMessageORM)
            .filter(ChatMessageORM.channel_name == channel_name)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
            .all()
        )[::-1]
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in rows]

    def top_chat_users(self, db: Session, limit: int, date_from: datetime | None, date_to: datetime | None) -> Sequence[Tuple[str, str, int]]:
        count_expr = func.count(ChatMessageORM.id).label("message_count")
        query = db.query(ChatMessageORM.channel_name, ChatMessageORM.user_name, count_expr)

        if date_from:
            query = query.filter(ChatMessageORM.created_at >= date_from)
        if date_to:
            query = query.filter(ChatMessageORM.created_at <= date_to)

        query = query.group_by(ChatMessageORM.channel_name, ChatMessageORM.user_name).order_by(count_expr.desc()).limit(limit)
        rows = query.all()
        return [(row.channel_name, row.user_name, row.message_count) for row in rows]

    def get_last_chat_messages_since(self, db: Session, channel_name: str, since: datetime) -> list[ChatMessage]:
        rows = (
            db.query(ChatMessageORM)
            .filter(ChatMessageORM.channel_name == channel_name)
            .filter(ChatMessageORM.created_at >= since)
            .order_by(ChatMessageORM.created_at.asc())
            .all()
        )
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in rows]