from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.stream.application.stream_service_provider import StreamServiceProvider
from app.twitch.application.background.viewer_time.model import ViewerTimeDTO
from app.viewer.application.viewer_service_provider import ViewerServiceProvider
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from core.provider import Provider


class HandleViewerTimeUseCase:

    def __init__(
        self,
        viewer_service_provider: ViewerServiceProvider,
        stream_service_provider: StreamServiceProvider,
        economy_service_provider: Provider[EconomyService],
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
    ):
        self._viewer_service_provider = viewer_service_provider
        self._stream_service_provider = stream_service_provider
        self._economy_service_provider = economy_service_provider
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        viewer_time_dto: ViewerTimeDTO,
    ):
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(viewer_time_dto.channel_name)

        if not active_stream:
            return

        with db_session_provider() as db:
            self._viewer_service_provider.get(db).check_inactive_viewers(active_stream.id, viewer_time_dto.occurred_at)

        broadcaster_id = await self._user_cache.get_user_id(viewer_time_dto.channel_name)
        moderator_id = await self._user_cache.get_user_id(viewer_time_dto.bot_nick or viewer_time_dto.channel_name)
        chatters = await self._twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
        if chatters:
            with db_session_provider() as db:
                self._viewer_service_provider.get(db).update_viewers(
                    active_stream_id=active_stream.id,
                    channel_name=viewer_time_dto.channel_name,
                    chatters=chatters,
                    current_time=viewer_time_dto.occurred_at
                )

        with db_readonly_session_provider() as db:
            viewers_count = self._viewer_service_provider.get(db).get_stream_watchers_count(active_stream.id)

        if viewers_count > active_stream.max_concurrent_viewers:
            with db_session_provider() as db:
                self._stream_service_provider.get(db).update_max_concurrent_viewers_count(active_stream.id, viewers_count)

        with db_session_provider() as db:
            viewer_sessions = self._viewer_service_provider.get(db).get_stream_viewer_sessions(active_stream.id)
            for session in viewer_sessions:
                available_rewards = self._viewer_service_provider.get(db).get_available_rewards(session)
                for minutes_threshold, reward_amount in available_rewards:
                    claimed_list = session.get_claimed_rewards_list()
                    claimed_list.append(minutes_threshold)
                    rewards = ",".join(map(str, sorted(claimed_list)))
                    self._viewer_service_provider.get(db).update_session_rewards(
                        session_id=session.id,
                        rewards=rewards,
                        current_time=viewer_time_dto.occurred_at or datetime.utcnow()
                    )
                    self._economy_service_provider.get(db).add_balance(
                        channel_name=viewer_time_dto.channel_name,
                        user_name=session.user_name,
                        amount=reward_amount,
                        transaction_type=TransactionType.VIEWER_TIME_REWARD,
                        description=f"Награда за {minutes_threshold} минут просмотра стрима"
                    )
