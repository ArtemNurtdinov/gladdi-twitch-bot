from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.stream.data.db.stream import Stream
from app.stream.domain.models import StreamInfo, StreamViewerSessionInfo
from app.stream.domain.repo import StreamRepository
from app.stream.application.mappers.stream_mapper import map_stream_row
from app.viewer.data.db.viewer_session import StreamViewerSession


class StreamRepositoryImpl(StreamRepository[Session]):

    def start_new_stream(self, db: Session, channel_name: str, started_at: datetime, game_name: str | None, title: str | None) -> None:
        stream = Stream(channel_name=channel_name, started_at=started_at, game_name=game_name, title=title, is_active=True)
        db.add(stream)

    def get_active_stream(self, db: Session, channel_name: str) -> Optional[StreamInfo]:
        row = db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()
        return map_stream_row(row)

    def end_stream(self, db: Session, active_stream_id: int, finish_time: datetime) -> None:
        stream = db.query(Stream).filter_by(id=active_stream_id).first()
        if not stream:
            return
        stream.ended_at = finish_time
        stream.is_active = False
        stream.updated_at = datetime.utcnow()

    def update_stream_total_viewers(self, db: Session, stream_id: int, total_viewers: int) -> None:
        stream = db.query(Stream).filter_by(id=stream_id).first()
        if not stream:
            return
        stream.total_viewers = total_viewers
        stream.updated_at = datetime.utcnow()

    def update_stream_metadata(self, db: Session, stream_id: int, game_name: str | None, title: str | None) -> None:
        stream = db.query(Stream).filter_by(id=stream_id).first()
        if not stream:
            return
        if game_name is not None:
            stream.game_name = game_name
        if title is not None:
            stream.title = title
        stream.updated_at = datetime.utcnow()

    def update_max_concurrent_viewers_count(self, db: Session, active_stream_id: int, viewers_count: int) -> None:
        stream = db.query(Stream).filter_by(id=active_stream_id).first()
        if not stream:
            return
        stream.max_concurrent_viewers = viewers_count
        stream.updated_at = datetime.utcnow()

    def list_streams(self, db: Session, skip: int, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> tuple[list[StreamInfo], int]:
        query = db.query(Stream)
        if date_from:
            query = query.filter(Stream.started_at >= date_from)
        if date_to:
            query = query.filter(Stream.started_at <= date_to)
        total = query.count()
        streams = query.order_by(Stream.started_at.desc()).offset(skip).limit(limit).all()
        items = [map_stream_row(row) for row in streams]
        return items, total

    def get_stream_with_sessions(self, db: Session, stream_id: int) -> Optional[tuple[StreamInfo, list[StreamViewerSessionInfo]]]:
        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if not stream:
            return None
        sessions = (
            db.query(StreamViewerSession)
            .filter(StreamViewerSession.stream_id == stream_id)
            .order_by(desc(StreamViewerSession.last_activity))
            .all()
        )
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
