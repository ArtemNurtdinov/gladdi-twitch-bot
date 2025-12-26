import logging
from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.stream.domain.stream_service import StreamService
from app.twitch.application.background.viewer_time.dto import ViewerTimeDTO
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.viewer.domain.viewer_session_service import ViewerTimeService

logger = logging.getLogger(__name__)


class HandleViewerTimeUseCase:

    def __init__(
        self,
        viewer_service_factory: Callable[[Session], ViewerTimeService],
        stream_service_factory: Callable[[Session], StreamService],
        economy_service_factory: Callable[[Session], EconomyService],
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
    ):
        self._viewer_service_factory = viewer_service_factory
        self._stream_service_factory = stream_service_factory
        self._economy_service_factory = economy_service_factory
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        viewer_time_dto: ViewerTimeDTO,
    ) -> None:
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_factory(db).get_active_stream(viewer_time_dto.channel_name)

        if not active_stream:
            return

        with db_session_provider() as db:
            self._viewer_service_factory(db).check_inactive_viewers(active_stream.id, viewer_time_dto.occurred_at)

        broadcaster_id = await self._user_cache.get_user_id(viewer_time_dto.channel_name)
        moderator_id = await self._user_cache.get_user_id(viewer_time_dto.bot_nick or viewer_time_dto.channel_name)
        chatters = await self._twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
        if chatters:
            with db_session_provider() as db:
                self._viewer_service_factory(db).update_viewers(
                    active_stream_id=active_stream.id,
                    channel_name=viewer_time_dto.channel_name,
                    chatters=chatters,
                    current_time=viewer_time_dto.occurred_at
                )

        with db_readonly_session_provider() as db:
            viewers_count = self._viewer_service_factory(db).get_stream_watchers_count(active_stream.id)

        if viewers_count > active_stream.max_concurrent_viewers:
            with db_session_provider() as db:
                self._stream_service_factory(db).update_max_concurrent_viewers_count(active_stream.id, viewers_count)

        with db_session_provider() as db:
            viewer_sessions = self._viewer_service_factory(db).get_stream_viewer_sessions(active_stream.id)
            for session in viewer_sessions:
                available_rewards = self._viewer_service_factory(db).get_available_rewards(session)
                for minutes_threshold, reward_amount in available_rewards:
                    claimed_list = session.get_claimed_rewards_list()
                    claimed_list.append(minutes_threshold)
                    rewards = ",".join(map(str, sorted(claimed_list)))
                    self._viewer_service_factory(db).update_session_rewards(
                        session.id, rewards, viewer_time_dto.occurred_at or datetime.utcnow()
                    )
                    description = f"Награда за {minutes_threshold} минут просмотра стрима"
                    self._economy_service_factory(db).add_balance(
                        viewer_time_dto.channel_name,
                        session.user_name,
                        reward_amount,
                        TransactionType.VIEWER_TIME_REWARD,
                        description,
                    )
