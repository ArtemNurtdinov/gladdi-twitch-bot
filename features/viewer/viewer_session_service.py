import logging
from typing import List
from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import joinedload, Session

from core.db import SessionLocal
from features.viewer.db.viewer_session import StreamViewerSession

logger = logging.getLogger(__name__)


class ViewerTimeService:
    STREAM_TIME_REWARDS = {
        30: 25,
        60: 50,
        90: 100,
        120: 150,
        150: 250,
        180: 350
    }
    ACTIVITY_TIMEOUT_MINUTES = 5
    CHECK_INTERVAL_SECONDS = 60

    def update_viewer_session(self, db: Session, stream_id: int, channel_name: str, user_name: str) -> None:
        session = db.query(StreamViewerSession).filter_by(stream_id=stream_id, user_name=user_name, channel_name=channel_name).first()

        current_time = datetime.utcnow()

        if session:
            session.last_activity = current_time
            session.updated_at = current_time

            if not session.is_watching:
                session.is_watching = True
                session.session_start = current_time
        else:
            session = StreamViewerSession(stream_id=stream_id, channel_name=channel_name, user_name=user_name, session_start=current_time, last_activity=current_time,
                                          is_watching=True)
            db.add(session)
            logger.debug(f"Создана новая сессия просмотра: {user_name} -> стрим {stream_id}")

    def update_viewers(self, db: Session, active_stream_id: int, channel_name: str, chatters: List[str]):
        current_time = datetime.utcnow()

        for user_name in chatters:
            normalized_user_name = user_name.lower()
            session = db.query(StreamViewerSession).filter_by(stream_id=active_stream_id, user_name=normalized_user_name, channel_name=channel_name).first()

            if not session:
                session = StreamViewerSession(stream_id=active_stream_id, channel_name=channel_name, user_name=normalized_user_name,
                                              session_start=current_time, last_activity=current_time, is_watching=True)
                db.add(session)
            else:
                session.last_activity = current_time
                session.updated_at = current_time

                if not session.is_watching:
                    session.is_watching = True
                    session.session_start = current_time

    def check_inactive_viewers(self, db: Session, active_stream_id: int) -> List[str]:
        inactive_users = []
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.ACTIVITY_TIMEOUT_MINUTES)
        inactive_sessions = db.query(StreamViewerSession).filter_by(stream_id=active_stream_id, is_watching=True).filter(StreamViewerSession.last_activity < cutoff_time).all()
        for session in inactive_sessions:
            inactive_users.append(session.user_name)

            if session.session_start:
                session_duration = datetime.utcnow() - session.session_start
                session_minutes = int(session_duration.total_seconds() / 60)
                session.total_minutes += session_minutes

            session.session_end = datetime.utcnow()
            session.is_watching = False
            session.updated_at = datetime.utcnow()

            logger.debug(f"Пользователь {session.user_name} помечен как неактивный в стриме {active_stream_id}")

        return inactive_users

    def get_stream_viewer_sessions(self, db: Session, stream_id: int) -> list[StreamViewerSession]:
        return db.query(StreamViewerSession).filter_by(stream_id=stream_id).all()

    def get_user_sessions(self, db: Session, channel_name: str, user_name: str) -> List[StreamViewerSession]:
        return (
            db.query(StreamViewerSession)
            .options(joinedload(StreamViewerSession.stream))
            .filter_by(channel_name=channel_name, user_name=user_name)
            .order_by(desc(StreamViewerSession.session_start))
            .all()
        )

    def get_available_rewards(self, session: StreamViewerSession) -> List[tuple]:
        available_rewards = []

        if session.is_watching and session.session_start:
            duration = datetime.utcnow() - session.session_start
            current_session_minutes = int(duration.total_seconds() / 60)
        else:
            current_session_minutes = 0

        total_minutes = session.total_minutes + current_session_minutes
        claimed_rewards = set(session.get_claimed_rewards_list())

        for minutes_threshold in sorted(self.STREAM_TIME_REWARDS.keys()):
            if total_minutes >= minutes_threshold and minutes_threshold not in claimed_rewards:
                reward_amount = self.STREAM_TIME_REWARDS[minutes_threshold]
                available_rewards.append((minutes_threshold, reward_amount))

        return available_rewards

    def get_stream_watchers_count(self, db: Session, active_stream_id: int) -> int:
        return db.query(StreamViewerSession).filter_by(stream_id=active_stream_id, is_watching=True).count()

    def finish_stream_sessions(self, db: Session, stream_id: int):
        active_sessions = db.query(StreamViewerSession).filter_by(stream_id=stream_id, is_watching=True).all()
        for session in active_sessions:
            if session.session_start:
                session_duration = datetime.utcnow() - session.session_start
                session_minutes = int(session_duration.total_seconds() / 60)
                session.total_minutes += session_minutes

            session.session_end = datetime.utcnow()
            session.is_watching = False
            session.updated_at = datetime.utcnow()

    def get_unique_viewers_count(self, db: Session, stream_id: int) -> int:
        return db.query(StreamViewerSession.user_name).filter_by(stream_id=stream_id).distinct().count()
