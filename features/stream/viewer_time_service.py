import logging
from typing import List
from datetime import datetime, timedelta

from db.base import SessionLocal
from features.stream.db.stream_viewer_session import StreamViewerSession

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

    def update_viewer_session(self, stream_id: int, channel_name: str, user_name: str) -> None:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            session = db.query(StreamViewerSession).filter_by(stream_id=stream_id, user_name=normalized_user_name, channel_name=channel_name).first()

            current_time = datetime.utcnow()

            if session:
                session.last_activity = current_time
                session.updated_at = current_time

                if not session.is_watching:
                    session.is_watching = True
                    session.session_start = current_time
                    logger.debug(f"Возобновлен просмотр: {normalized_user_name} -> стрим {stream_id}")
            else:
                session = StreamViewerSession(stream_id=stream_id, channel_name=channel_name, user_name=normalized_user_name, session_start=current_time,
                                              last_activity=current_time, is_watching=True)
                db.add(session)
                logger.debug(f"Создана новая сессия просмотра: {normalized_user_name} -> стрим {stream_id}")

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении активности для {user_name}: {e}")
        finally:
            db.close()

    def update_viewers(self, active_stream_id: int, channel_name: str, chatters: List[str]):
        db = SessionLocal()
        try:
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
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении зрителей через API: {e}")
        finally:
            db.close()

    def check_inactive_viewers(self, active_stream_id: int) -> List[str]:
        inactive_users = []

        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.ACTIVITY_TIMEOUT_MINUTES)

            inactive_sessions = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=active_stream_id, is_watching=True)
                .filter(StreamViewerSession.last_activity < cutoff_time)
                .all()
            )

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
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при проверке неактивных зрителей: {e}")
        finally:
            db.close()

        return inactive_users

    def get_stream_viewer_sessions(self, stream_id: int) -> list[StreamViewerSession]:
        db = SessionLocal()
        try:
            return db.query(StreamViewerSession).filter_by(stream_id=stream_id).all()
        finally:
            db.close()

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

    def get_stream_watchers_count(self, active_stream_id: int) -> int:
        db = SessionLocal()
        try:
            return db.query(StreamViewerSession).filter_by(stream_id=active_stream_id, is_watching=True).count()
        finally:
            db.close()

    def finish_stream_sessions(self, stream_id: int):
        db = SessionLocal()
        try:
            active_sessions = db.query(StreamViewerSession).filter_by(stream_id=stream_id, is_watching=True).all()
            for session in active_sessions:
                if session.session_start:
                    session_duration = datetime.utcnow() - session.session_start
                    session_minutes = int(session_duration.total_seconds() / 60)
                    session.total_minutes += session_minutes

                session.session_end = datetime.utcnow()
                session.is_watching = False
                session.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при закрытии сессий стрима: {e}")
            return None
        finally:
            db.close()

    def get_unique_viewers_count(self, stream_id: int) -> int:
        db = SessionLocal()
        try:
            return db.query(StreamViewerSession.user_name).filter_by(stream_id=stream_id).distinct().count()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при получении кол-ва уникальных зрителей стрима: {e}")
        finally:
            db.close()
