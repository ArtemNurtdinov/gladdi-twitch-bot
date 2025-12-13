import logging
from typing import Dict, List
from datetime import datetime, timedelta

from db.database import SessionLocal
from features.stream.db.stream_viewer_session import StreamViewerSession
from features.economy.db.transaction_history import TransactionType
from features.economy.economy_service import EconomyService
from features.stream.stream_service import StreamService

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

    def __init__(self, economy_service: EconomyService, stream_service: StreamService):
        self.economy_service = economy_service
        self.stream_service = stream_service

    def update_activity(self, channel_name: str, user_name: str) -> None:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            active_stream = self.stream_service.get_active_stream(channel_name)
            if not active_stream:
                logger.debug(f"Нет активного стрима для обновления активности {user_name}")
                return

            session = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=active_stream.id, user_name=normalized_user_name, channel_name=channel_name)
                .first()
            )

            current_time = datetime.utcnow()

            if not session:
                session = StreamViewerSession(stream_id=active_stream.id, channel_name=channel_name, user_name=normalized_user_name, session_start=current_time,
                                              last_activity=current_time, is_watching=True)
                db.add(session)
                logger.debug(f"Создана новая сессия просмотра: {normalized_user_name} -> стрим {active_stream.id}")
            else:
                session.last_activity = current_time
                session.updated_at = current_time

                if not session.is_watching:
                    session.is_watching = True
                    session.session_start = current_time
                    logger.debug(f"Возобновлен просмотр: {normalized_user_name} -> стрим {active_stream.id}")

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении активности для {user_name}: {e}")
        finally:
            db.close()

    async def update_viewers(self, channel_name: str, chatters: List[str]) -> None:
        if not chatters:
            return

        active_stream = self.stream_service.get_active_stream(channel_name)
        if not active_stream:
            logger.debug("Нет активного стрима для обновления через API")
            return

        db = SessionLocal()
        try:
            current_time = datetime.utcnow()

            for user_name in chatters:
                normalized_user_name = user_name.lower()

                session = (
                    db.query(StreamViewerSession)
                    .filter_by(stream_id=active_stream.id, user_name=normalized_user_name, channel_name=channel_name)
                    .first()
                )

                if not session:
                    session = StreamViewerSession(stream_id=active_stream.id, channel_name=channel_name, user_name=normalized_user_name,
                                                  session_start=current_time, last_activity=current_time, is_watching=True)
                    db.add(session)
                else:
                    session.last_activity = current_time
                    session.updated_at = current_time

                    if not session.is_watching:
                        session.is_watching = True
                        session.session_start = current_time

            db.commit()
            logger.debug(f"API: Обновлена активность для {len(chatters)} зрителей в стриме {active_stream.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении зрителей через API: {e}")
        finally:
            db.close()

    def check_inactive_viewers(self, channel_name: str) -> List[str]:
        active_stream = self.stream_service.get_active_stream(channel_name)
        if not active_stream:
            return []

        db = SessionLocal()
        inactive_users = []

        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.ACTIVITY_TIMEOUT_MINUTES)

            inactive_sessions = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=active_stream.id, is_watching=True)
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

                logger.debug(f"Пользователь {session.user_name} помечен как неактивный в стриме {active_stream.id}")

            db.commit()

            if inactive_users:
                logger.info(f"Найдено {len(inactive_users)} неактивных зрителей в стриме {active_stream.id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при проверке неактивных зрителей: {e}")
        finally:
            db.close()

        return inactive_users

    def check_and_grant_rewards(self, channel_name: str) -> List[Dict]:
        active_stream = self.stream_service.get_active_stream(channel_name)
        if not active_stream:
            return []

        db = SessionLocal()
        rewards_granted = []

        try:
            sessions = (
                db.query(StreamViewerSession)
                .filter_by(stream_id=active_stream.id)
                .all()
            )

            for session in sessions:
                available_rewards = self._get_available_rewards(session)

                for minutes_threshold, reward_amount in available_rewards:
                    try:
                        session.add_reward(minutes_threshold)
                        session.updated_at = datetime.utcnow()

                        self.economy_service.add_balance_with_session(db, channel_name, session.user_name, reward_amount, TransactionType.VIEWER_TIME_REWARD,
                                                                      f"Награда за {minutes_threshold} минут просмотра стрима")
                        rewards_granted.append({
                            "user_name": session.user_name,
                            "minutes": minutes_threshold,
                            "reward": reward_amount,
                            "stream_id": active_stream.id
                        })

                        logger.info(f"Награда выдана: {session.user_name} получил {reward_amount} монет за {minutes_threshold} минут просмотра стрима {active_stream.id}")
                    except Exception as e:
                        logger.error(f"Ошибка при выдаче награды пользователю {session.user_name}: {e}")

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при проверке и выдаче наград: {e}")
        finally:
            db.close()

        return rewards_granted

    def _get_available_rewards(self, session: StreamViewerSession) -> List[tuple]:
        available_rewards = []
        total_minutes = session.get_total_minutes_with_current()
        claimed_rewards = set(session.get_claimed_rewards_list())

        for minutes_threshold in sorted(self.STREAM_TIME_REWARDS.keys()):
            if (total_minutes >= minutes_threshold and
                minutes_threshold not in claimed_rewards):
                reward_amount = self.STREAM_TIME_REWARDS[minutes_threshold]
                available_rewards.append((minutes_threshold, reward_amount))

        return available_rewards
