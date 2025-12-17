import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from features.stream.db.stream import Stream
from features.stream.stream_schemas import StreamListResponse
from features.viewer.db.viewer_session import StreamViewerSession

logger = logging.getLogger(__name__)


class StreamService:

    def create_stream(self, db: Session, channel_name: str, started_at: datetime, game_name: str = None, title: str = None):
        active_stream = self.get_active_stream(db, channel_name)
        if active_stream:
            logger.warning(f"Попытка начать стрим, но активный стрим уже существует: {active_stream.id}")
            return active_stream

        stream = Stream(channel_name=channel_name, started_at=started_at, game_name=game_name, title=title, is_active=True)
        db.add(stream)

    def end_stream(self, db: Session, active_stream_id: int, finish_time: datetime):
        stream = db.query(Stream).filter_by(id=active_stream_id).first()
        stream.ended_at = finish_time
        stream.is_active = False
        stream.updated_at = datetime.utcnow()

    def update_stream_total_viewers(self, db: Session, stream_id: int, total_viewers: int):
        stream = db.query(Stream).filter_by(id=stream_id).first()
        stream.total_viewers = total_viewers
        stream.updated_at = datetime.utcnow()

    def get_active_stream(self, db: Session, channel_name: str) -> Optional[Stream]:
        return db.query(Stream).filter_by(channel_name=channel_name, is_active=True).first()

    def update_stream_metadata(self, db: Session, stream_id: int, game_name: str = None, title: str = None):
        stream = db.query(Stream).filter_by(id=stream_id).first()

        if game_name is not None:
            stream.game_name = game_name
        if title is not None:
            stream.title = title

        stream.updated_at = datetime.utcnow()

    def update_max_concurrent_viewers_count(self, db: Session, active_stream_id: int, viewers_count: int):
        stream = db.query(Stream).filter_by(id=active_stream_id).first()
        stream.max_concurrent_viewers = viewers_count
        stream.updated_at = datetime.utcnow()

    def get_streams(self, db: Session, skip: int, limit: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> StreamListResponse:
        query = db.query(Stream)
        if date_from:
            query = query.filter(Stream.started_at >= date_from)
        if date_to:
            query = query.filter(Stream.started_at <= date_to)
        total = query.count()
        streams = query.order_by(Stream.started_at.desc()).offset(skip).limit(limit).all()
        return StreamListResponse(items=streams, total=total)

    def get_stream_by_id(self, db: Session, stream_id: int) -> Optional[Stream]:
        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if not stream:
            return None

        sessions = db.query(StreamViewerSession).filter(StreamViewerSession.stream_id == stream_id).order_by(desc(StreamViewerSession.last_activity)).all()
        stream.viewer_sessions = sessions
        return stream
