import asyncio
import logging
from datetime import datetime
from typing import Callable, Any

from app.economy.domain.models import TransactionType
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from core.background_task_runner import BackgroundTaskRunner
from core.db import SessionLocal, db_ro_session

logger = logging.getLogger(__name__)


class ViewerTimeJob:
    name = "check_viewer_time"

    def __init__(
        self,
        channel_name: str,
        viewer_service_factory: Callable[[Any], Any],
        stream_service_factory: Callable[[Any], Any],
        economy_service_factory: Callable[[Any], Any],
        user_cache: Any,
        twitch_api_service: TwitchApiService,
        bot_nick_provider: Callable[[], str],
        check_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._viewer_service_factory = viewer_service_factory
        self._stream_service_factory = stream_service_factory
        self._economy_service_factory = economy_service_factory
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._bot_nick_provider = bot_nick_provider
        self._interval_seconds = check_interval_seconds

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                with db_ro_session() as db:
                    active_stream = self._stream_service_factory(db).get_active_stream(self._channel_name)

                if not active_stream:
                    await asyncio.sleep(self._interval_seconds)
                    continue

                with SessionLocal.begin() as db:
                    self._viewer_service_factory(db).check_inactive_viewers(active_stream.id, datetime.utcnow())

                broadcaster_id = await self._user_cache.get_user_id(self._channel_name)
                moderator_login = self._bot_nick_provider()
                moderator_id = await self._user_cache.get_user_id(moderator_login)
                chatters = await self._twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
                if chatters:
                    with SessionLocal.begin() as db:
                        self._viewer_service_factory(db).update_viewers(active_stream.id, self._channel_name, chatters, datetime.utcnow())

                with db_ro_session() as db:
                    viewers_count = self._viewer_service_factory(db).get_stream_watchers_count(active_stream.id)

                if viewers_count > active_stream.max_concurrent_viewers:
                    with SessionLocal.begin() as db:
                        self._stream_service_factory(db).update_max_concurrent_viewers_count(active_stream.id, viewers_count)

                with SessionLocal.begin() as db:
                    viewer_sessions = self._viewer_service_factory(db).get_stream_viewer_sessions(active_stream.id)
                    for session in viewer_sessions:
                        available_rewards = self._viewer_service_factory(db).get_available_rewards(session)
                        for minutes_threshold, reward_amount in available_rewards:
                            claimed_list = session.get_claimed_rewards_list()
                            claimed_list.append(minutes_threshold)
                            rewards = ",".join(map(str, sorted(claimed_list)))
                            self._viewer_service_factory(db).update_session_rewards(session.id, rewards, datetime.utcnow())
                            description = f"Награда за {minutes_threshold} минут просмотра стрима"
                            self._economy_service_factory(db).add_balance(
                                self._channel_name,
                                session.user_name,
                                reward_amount,
                                TransactionType.VIEWER_TIME_REWARD,
                                description,
                            )

            except asyncio.CancelledError:
                logger.info("ViewerTimeJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ViewerTimeJob: {e}")

            await asyncio.sleep(self._interval_seconds)
