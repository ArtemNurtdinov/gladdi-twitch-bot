from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from features.stream.db.stream import Stream
from features.stream.domain.models import StreamInfo
from features.stream.domain.repo import StreamRepository
from features.viewer.db.viewer_session import StreamViewerSession


class StreamRepositoryImpl(StreamRepository[Session]):

    def create_stream(self, db: Session, channel_name: str, started_at: datetime, game_name: str | None, title: str | None) -> None:
        stream = Stream(channel_name=channel_name, started_at=started_at, game_name=game_name, title=title, is_active=True)
        db.add(stream)

    def get_active_stream(self, db: Session, channel_name: str) -> Optional[StreamInfo]:
        row = db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()
        if not row:
            return None
        return StreamInfo(
            id=row.id,
            channel_name=row.channel_name,
            started_at=row.started_at,
            ended_at=row.ended_at,
            game_name=row.game_name,
            title=row.title,
            is_active=row.is_active,
            max_concurrent_viewers=row.max_concurrent_viewers,
            total_viewers=row.total_viewers,
        )

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

    def list_streams(self, db: Session, skip: int, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> Tuple[Sequence[Stream], int]:
        query = db.query(Stream)
        if date_from:
            query = query.filter(Stream.started_at >= date_from)
        if date_to:
            query = query.filter(Stream.started_at <= date_to)
        total = query.count()
        streams = query.order_by(Stream.started_at.desc()).offset(skip).limit(limit).all()
        return streams, total

    def get_stream_with_sessions(self, db: Session, stream_id: int) -> Optional[Tuple[Stream, Sequence[StreamViewerSession]]]:
        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if not stream:
            return None
        sessions = (
            db.query(StreamViewerSession)
            .filter(StreamViewerSession.stream_id == stream_id)
            .order_by(desc(StreamViewerSession.last_activity))
            .all()
        )
        return stream, sessions
