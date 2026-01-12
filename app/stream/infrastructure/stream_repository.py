from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.stream.domain.models import StreamInfo, StreamViewerSessionInfo
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.db.stream import Stream
from app.stream.infrastructure.mappers.stream_mapper import map_stream_row
from app.viewer.data.db.viewer_session import StreamViewerSession


class StreamRepositoryImpl(StreamRepository):
    def __init__(self, db: Session):
        self._db = db

    def start_new_stream(self, channel_name: str, started_at: datetime, game_name: str | None, title: str | None) -> None:
        stream = Stream(channel_name=channel_name, started_at=started_at, game_name=game_name, title=title, is_active=True)
        self._db.add(stream)

    def get_active_stream(self, channel_name: str) -> StreamInfo | None:
        stmt = (
            select(Stream)
            .where(Stream.channel_name == channel_name)
            .where(Stream.is_active.is_(True))
        )
        row = self._db.execute(stmt).scalars().first()
        if not row:
            return None
        return map_stream_row(row)

    def end_stream(self, active_stream_id: int, finish_time: datetime) -> None:
        stmt = select(Stream).where(Stream.id == active_stream_id)
        stream = self._db.execute(stmt).scalars().first()
        if not stream:
            return
        stream.ended_at = finish_time
        stream.is_active = False
        stream.updated_at = datetime.utcnow()

    def update_stream_total_viewers(self, stream_id: int, total_viewers: int) -> None:
        stmt = select(Stream).where(Stream.id == stream_id)
        stream = self._db.execute(stmt).scalars().first()
        if not stream:
            return
        stream.total_viewers = total_viewers
        stream.updated_at = datetime.utcnow()

    def update_stream_metadata(self, stream_id: int, game_name: str | None, title: str | None) -> None:
        stmt = select(Stream).where(Stream.id == stream_id)
        stream = self._db.execute(stmt).scalars().first()
        if not stream:
            return
        if game_name is not None:
            stream.game_name = game_name
        if title is not None:
            stream.title = title
        stream.updated_at = datetime.utcnow()

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int) -> None:
        stmt = select(Stream).where(Stream.id == active_stream_id)
        stream = self._db.execute(stmt).scalars().first()
        if not stream:
            return
        stream.max_concurrent_viewers = viewers_count
        stream.updated_at = datetime.utcnow()

    def list_streams(
        self, skip: int, limit: int, date_from: datetime | None, date_to: datetime | None
    ) -> tuple[list[StreamInfo], int]:
        base_stmt = select(Stream)
        count_stmt = select(func.count()).select_from(Stream)
        if date_from:
            base_stmt = base_stmt.where(Stream.started_at >= date_from)
            count_stmt = count_stmt.where(Stream.started_at >= date_from)
        if date_to:
            base_stmt = base_stmt.where(Stream.started_at <= date_to)
            count_stmt = count_stmt.where(Stream.started_at <= date_to)

        total = self._db.execute(count_stmt).scalar_one()

        stmt = base_stmt.order_by(Stream.started_at.desc()).offset(skip).limit(limit)
        streams = self._db.execute(stmt).scalars().all()
        items = [map_stream_row(row) for row in streams]
        return items, total

    def get_stream_with_sessions(self, stream_id: int) -> tuple[StreamInfo, list[StreamViewerSessionInfo]] | None:
        stream_stmt = select(Stream).where(Stream.id == stream_id)
        stream = self._db.execute(stream_stmt).scalars().first()
        if not stream:
            return None

        sessions_stmt = (
            select(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .order_by(desc(StreamViewerSession.last_activity))
        )
        sessions = self._db.execute(sessions_stmt).scalars().all()
        return (
            map_stream_row(stream),
            [
                StreamViewerSessionInfo(
                    id=s.id,
                    stream_id=s.stream_id,
                    channel_name=s.channel_name,
                    user_name=s.user_name,
                    session_start=s.session_start,
                    session_end=s.session_end,
                    total_minutes=s.total_minutes,
                    last_activity=s.last_activity,
                    is_watching=s.is_watching,
                    rewards_claimed=s.rewards_claimed,
                    last_reward_claimed=s.last_reward_claimed,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in sessions
            ],
        )
