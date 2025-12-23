from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.stream.data.mappers.stream_mapper import map_stream_row

from app.viewer.data.db.viewer_session import StreamViewerSession
from app.viewer.domain.models import ViewerSession
from app.viewer.domain.repo import ViewerRepository


class ViewerRepositoryImpl(ViewerRepository):
    ACTIVITY_TIMEOUT_MINUTES = 5

    def __init__(self, db: Session):
        self._db = db

    def _to_viewer_session(self, row: StreamViewerSession) -> ViewerSession:
        return ViewerSession(
            id=row.id,
            stream_id=row.stream_id,
            channel_name=row.channel_name,
            user_name=row.user_name,
            session_start=row.session_start,
            session_end=row.session_end,
            total_minutes=row.total_minutes,
            last_activity=row.last_activity,
            is_watching=row.is_watching,
            rewards_claimed=row.rewards_claimed,
            last_reward_claimed=row.last_reward_claimed,
            created_at=row.created_at,
            updated_at=row.updated_at,
            stream=map_stream_row(row.stream) if row.stream else None
        )

    def get_viewer_session(self, stream_id: int, channel_name: str, user_name: str) -> Optional[ViewerSession]:
        row = self._db.query(StreamViewerSession).filter_by(stream_id=stream_id, user_name=user_name, channel_name=channel_name).first()
        if not row:
            return None
        return self._to_viewer_session(row)

    def create_view_session(self, stream_id: int, channel_name: str, user_name: str, current_time: datetime):
        session = StreamViewerSession(
            stream_id=stream_id,
            channel_name=channel_name,
            user_name=user_name,
            session_start=current_time,
            last_activity=current_time,
            is_watching=True
        )
        self._db.add(session)

    def update_last_activity(self, stream_id: int, channel_name: str, user_name: str, current_time: datetime):
        session = self._db.query(StreamViewerSession).filter_by(stream_id=stream_id, user_name=user_name, channel_name=channel_name).first()
        session.last_activity = current_time
        session.updated_at = current_time
        session.is_watching = True

    def get_inactive_sessions(self, stream_id: int, current_time: datetime) -> list[ViewerSession]:
        cutoff_time = current_time - timedelta(minutes=self.ACTIVITY_TIMEOUT_MINUTES)
        rows = (
            self._db.query(StreamViewerSession)
            .filter_by(
                stream_id=stream_id,
                is_watching=True
            )
            .filter(StreamViewerSession.last_activity < cutoff_time)
            .all()
        )
        return [self._to_viewer_session(row) for row in rows]

    def finish_session(
        self,
        stream_id: int,
        channel_name: str,
        user_name: str,
        total_minutes: int,
        current_time: datetime
    ):
        session = self._db.query(StreamViewerSession).filter_by(stream_id=stream_id, user_name=user_name, channel_name=channel_name).first()
        session.total_minutes = total_minutes
        session.session_end = current_time
        session.is_watching = False
        session.updated_at = current_time

    def get_active_sessions(self, stream_id: int) -> list[ViewerSession]:
        rows = self._db.query(StreamViewerSession).filter_by(stream_id=stream_id, is_watching=True).all()
        return [self._to_viewer_session(row) for row in rows]

    def get_unique_viewers_count(self, stream_id: int) -> int:
        return self._db.query(StreamViewerSession.user_name).filter_by(stream_id=stream_id).distinct().count()

    def get_viewer_sessions(self, stream_id: int) -> list[ViewerSession]:
        rows = self._db.query(StreamViewerSession).filter_by(stream_id=stream_id).all()
        return [self._to_viewer_session(row) for row in rows]

    def update_session_rewards(self, session_id: int, rewards: str, current_time: datetime):
        row = self._db.query(StreamViewerSession).filter_by(id=session_id).first()
        if not row:
            return
        row.rewards_claimed = rewards
        row.last_reward_claimed = current_time
        row.updated_at = current_time

    def get_user_sessions(self, channel_name: str, user_name: str) -> list[ViewerSession]:
        rows = (
            self._db.query(StreamViewerSession)
            .options(joinedload(StreamViewerSession.stream))
            .filter_by(channel_name=channel_name, user_name=user_name)
            .order_by(desc(StreamViewerSession.session_start))
            .all()
        )
        return [self._to_viewer_session(row) for row in rows]

    def get_stream_watchers_count(self, stream_id: int) -> int:
        return self._db.query(StreamViewerSession).filter_by(stream_id=stream_id, is_watching=True).count()