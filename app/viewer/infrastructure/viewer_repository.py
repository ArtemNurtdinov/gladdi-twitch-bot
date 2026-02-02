from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.stream.infrastructure.mappers.stream_mapper import map_stream_row
from app.viewer.domain.models import ViewerSession
from app.viewer.domain.repo import ViewerRepository
from app.viewer.infrastructure.db.viewer_session import StreamViewerSession


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
            stream=map_stream_row(row.stream) if row.stream else None,
        )

    def get_viewer_session(self, stream_id: int, channel_name: str, user_name: str) -> ViewerSession | None:
        stmt = (
            select(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .where(StreamViewerSession.user_name == user_name)
            .where(StreamViewerSession.channel_name == channel_name)
        )
        row = self._db.execute(stmt).scalars().first()
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
            is_watching=True,
        )
        self._db.add(session)

    def update_last_activity(self, stream_id: int, channel_name: str, user_name: str, current_time: datetime):
        stmt = (
            select(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .where(StreamViewerSession.user_name == user_name)
            .where(StreamViewerSession.channel_name == channel_name)
        )
        session = self._db.execute(stmt).scalars().first()
        if not session:
            return
        session.last_activity = current_time
        session.updated_at = current_time
        session.is_watching = True

    def get_inactive_sessions(self, stream_id: int, current_time: datetime) -> list[ViewerSession]:
        cutoff_time = current_time - timedelta(minutes=self.ACTIVITY_TIMEOUT_MINUTES)
        stmt = (
            select(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .where(StreamViewerSession.is_watching.is_(True))
            .where(StreamViewerSession.last_activity < cutoff_time)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_viewer_session(row) for row in rows]

    def finish_session(self, stream_id: int, channel_name: str, user_name: str, total_minutes: int, current_time: datetime):
        stmt = (
            select(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .where(StreamViewerSession.user_name == user_name)
            .where(StreamViewerSession.channel_name == channel_name)
        )
        session = self._db.execute(stmt).scalars().first()
        if not session:
            return
        session.total_minutes = total_minutes
        session.session_end = current_time
        session.is_watching = False
        session.updated_at = current_time

    def get_active_sessions(self, stream_id: int) -> list[ViewerSession]:
        stmt = (
            select(StreamViewerSession).where(StreamViewerSession.stream_id == stream_id).where(StreamViewerSession.is_watching.is_(True))
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_viewer_session(row) for row in rows]

    def get_unique_viewers_count(self, stream_id: int) -> int:
        stmt = select(func.count(func.distinct(StreamViewerSession.user_name))).where(StreamViewerSession.stream_id == stream_id)
        return self._db.execute(stmt).scalar_one()

    def get_viewer_sessions(self, stream_id: int) -> list[ViewerSession]:
        stmt = select(StreamViewerSession).where(StreamViewerSession.stream_id == stream_id)
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_viewer_session(row) for row in rows]

    def update_session_rewards(self, session_id: int, rewards: str, current_time: datetime):
        stmt = select(StreamViewerSession).where(StreamViewerSession.id == session_id)
        row = self._db.execute(stmt).scalars().first()
        if not row:
            return
        row.rewards_claimed = rewards
        row.last_reward_claimed = current_time
        row.updated_at = current_time

    def get_user_sessions(self, channel_name: str, user_name: str) -> list[ViewerSession]:
        stmt = (
            select(StreamViewerSession)
            .options(joinedload(StreamViewerSession.stream))
            .where(StreamViewerSession.channel_name == channel_name)
            .where(StreamViewerSession.user_name == user_name)
            .order_by(desc(StreamViewerSession.session_start))
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_viewer_session(row) for row in rows]

    def get_stream_watchers_count(self, stream_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(StreamViewerSession)
            .where(StreamViewerSession.stream_id == stream_id)
            .where(StreamViewerSession.is_watching.is_(True))
        )
        return self._db.execute(stmt).scalar_one()
