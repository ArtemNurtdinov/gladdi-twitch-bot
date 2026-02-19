from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.chat.domain.models import ChatMessage
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.db.chat_message import ChatMessage as ChatMessageORM


class ChatRepositoryImpl(ChatRepository):
    def __init__(self, db: Session):
        self._db = db

    def save(self, message: ChatMessage) -> None:
        self._db.add(
            ChatMessageORM(
                channel_name=message.channel_name, user_name=message.user_name, content=message.content, created_at=message.created_at
            )
        )

    def list_between(self, channel_name: str, start: datetime, end: datetime) -> Sequence[ChatMessage]:
        stmt = (
            select(ChatMessageORM)
            .where(ChatMessageORM.channel_name == channel_name)
            .where(ChatMessageORM.created_at >= start)
            .where(ChatMessageORM.created_at < end)
            .order_by(ChatMessageORM.created_at.asc())
        )
        rows = self._db.execute(stmt).scalars().all()
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in rows]

    def list_last(self, channel_name: str, limit: int) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageORM)
            .where(ChatMessageORM.channel_name == channel_name)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in reversed(rows)]

    def top_chat_users(self, limit: int, date_from: datetime | None, date_to: datetime | None) -> Sequence[tuple[str, str, int]]:
        count_expr = func.count(ChatMessageORM.id).label("message_count")
        stmt = select(ChatMessageORM.channel_name, ChatMessageORM.user_name, count_expr)
        if date_from:
            stmt = stmt.where(ChatMessageORM.created_at >= date_from)
        if date_to:
            stmt = stmt.where(ChatMessageORM.created_at <= date_to)
        stmt = stmt.group_by(ChatMessageORM.channel_name, ChatMessageORM.user_name).order_by(count_expr.desc()).limit(limit)
        rows = self._db.execute(stmt).all()
        return [(row.channel_name, row.user_name, row.message_count) for row in rows]

    def get_last_chat_messages_since(self, channel_name: str, since: datetime) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageORM)
            .where(ChatMessageORM.channel_name == channel_name)
            .where(ChatMessageORM.created_at >= since)
            .order_by(ChatMessageORM.created_at.asc())
        )
        rows = self._db.execute(stmt).scalars().all()
        return [ChatMessage(r.channel_name, r.user_name, r.content, r.created_at) for r in rows]

    def count_between(self, channel_name: str, start: datetime, end: datetime) -> int:
        stmt = (
            select(func.count(ChatMessageORM.id))
            .where(ChatMessageORM.channel_name == channel_name)
            .where(ChatMessageORM.created_at >= start)
            .where(ChatMessageORM.created_at < end)
        )
        return self._db.execute(stmt).scalar() or 0
