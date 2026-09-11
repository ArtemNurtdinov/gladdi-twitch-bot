from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.periodic_message.domain.model.periodic_message import PeriodicMessage, PeriodicMessageCreate, PeriodicMessagePatch
from app.periodic_message.domain.repository import PeriodicMessageRepository
from app.periodic_message.infrastructure.db.periodic_message import PeriodicMessageRow
from app.periodic_message.infrastructure.mapper.periodic_message_mapper import PeriodicMessageMapper


class PeriodicMessageRepositoryImpl(PeriodicMessageRepository):
    def __init__(self, db: Session, mapper: PeriodicMessageMapper):
        self._db = db
        self._mapper = mapper

    def get_all_by_channel(self, channel_name: str) -> list[PeriodicMessage]:
        stmt = select(PeriodicMessageRow).where(PeriodicMessageRow.channel_name == channel_name).order_by(PeriodicMessageRow.id)
        rows = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(row) for row in rows]

    async def get_by_id(self, message_id: int) -> PeriodicMessage | None:
        row = self._db.get(PeriodicMessageRow, message_id)
        return self._mapper.map_to_domain(row) if row else None

    async def create(self, message: PeriodicMessageCreate) -> PeriodicMessage:
        row = self._mapper.map_create_to_db(message)
        self._db.add(row)
        self._db.flush()
        return self._mapper.map_to_domain(row)

    async def patch(self, message: PeriodicMessagePatch) -> PeriodicMessage | None:
        row = self._db.get(PeriodicMessageRow, message.id)
        if row is None:
            return None

        if message.content is not None:
            row.content = message.content
        if message.use_llm is not None:
            row.use_llm = message.use_llm
        if message.interval_minutes is not None:
            row.interval_minutes = message.interval_minutes
        if message.is_enabled is not None:
            row.is_enabled = message.is_enabled

        self._db.flush()
        return self._mapper.map_to_domain(row)

    async def delete(self, message_id: int) -> None:
        row = self._db.get(PeriodicMessageRow, message_id)
        if row is not None:
            self._db.delete(row)

    def get_due_enabled(self, channel_name: str, now: datetime) -> list[PeriodicMessage]:
        stmt = (
            select(PeriodicMessageRow)
            .where(PeriodicMessageRow.channel_name == channel_name)
            .where(PeriodicMessageRow.is_enabled.is_(True))
            .where(or_(PeriodicMessageRow.next_send_at.is_(None), PeriodicMessageRow.next_send_at <= now))
            .order_by(PeriodicMessageRow.id)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(row) for row in rows]

    async def update_schedule(self, message_id: int, last_sent_at: datetime, next_send_at: datetime) -> None:
        row = self._db.get(PeriodicMessageRow, message_id)
        if row is None:
            return
        row.last_sent_at = last_sent_at
        row.next_send_at = next_send_at
        self._db.flush()
