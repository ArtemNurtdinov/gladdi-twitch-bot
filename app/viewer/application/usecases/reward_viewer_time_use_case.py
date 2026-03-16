from datetime import datetime

from app.economy.domain.models import TransactionType
from app.platform.domain.repository import PlatformRepository
from app.user.application.ports.user_cache_port import UserCachePort
from app.viewer.application.models.viewer_time import ViewerTimeDTO
from app.viewer.application.uow.viewer_time_uow import ViewerTimeUnitOfWorkFactory


class RewardViewerTimeUseCase:
    STREAM_TIME_REWARDS = {30: 25, 60: 50, 90: 100, 120: 150, 150: 250, 180: 350}

    def __init__(
        self, reward_viewer_time_uow: ViewerTimeUnitOfWorkFactory, user_cache: UserCachePort, platform_repository: PlatformRepository
    ):
        self._reward_viewer_time_uow = reward_viewer_time_uow
        self._user_cache = user_cache
        self._platform_repository = platform_repository

    async def handle(self, viewer_time: ViewerTimeDTO):
        with self._reward_viewer_time_uow.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(viewer_time.channel_name)

        if not active_stream:
            return

        with self._reward_viewer_time_uow.create() as uow:
            inactive_users = []
            inactive_sessions = uow.viewer_repository.get_inactive_sessions(active_stream.id, viewer_time.occurred_at)
            for session in inactive_sessions:
                inactive_users.append(session.user_name)
                session_duration = datetime.utcnow() - session.session_start
                session_minutes = int(session_duration.total_seconds() / 60)
                total_minutes = session.total_minutes + session_minutes
                uow.viewer_repository.finish_session(
                    stream_id=active_stream.id,
                    channel_name=session.channel_name,
                    user_name=session.user_name,
                    total_minutes=total_minutes,
                    current_time=viewer_time.occurred_at,
                )

        broadcaster_id = await self._user_cache.get_user_id(viewer_time.channel_name)
        moderator_id = await self._user_cache.get_user_id(viewer_time.bot_nick or viewer_time.channel_name)
        chatters = await self._platform_repository.get_stream_chatters(broadcaster_id, moderator_id)
        if chatters:
            with self._reward_viewer_time_uow.create() as uow:
                for user_name in chatters:
                    normalized_user_name = user_name.lower()
                    session = uow.viewer_repository.get_viewer_session(active_stream.id, viewer_time.channel_name, normalized_user_name)
                    if session:
                        uow.viewer_repository.update_last_activity(
                            stream_id=active_stream.id,
                            channel_name=viewer_time.channel_name,
                            user_name=user_name,
                            current_time=viewer_time.occurred_at,
                        )
                    else:
                        uow.viewer_repository.create_view_session(
                            stream_id=active_stream.id,
                            channel_name=viewer_time.channel_name,
                            user_name=user_name,
                            current_time=viewer_time.occurred_at,
                        )

        with self._reward_viewer_time_uow.create(read_only=True) as uow:
            viewers_count = uow.viewer_repository.get_stream_watchers_count(active_stream.id)

        if viewers_count > active_stream.max_concurrent_viewers:
            with self._reward_viewer_time_uow.create() as uow:
                uow.stream_service.update_max_concurrent_viewers_count(active_stream.id, viewers_count)

        with self._reward_viewer_time_uow.create() as uow:
            viewer_sessions = uow.viewer_repository.get_viewer_sessions(active_stream.id)
            for session in viewer_sessions:
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

                for minutes_threshold, reward_amount in available_rewards:
                    claimed_list = session.get_claimed_rewards_list()
                    claimed_list.append(minutes_threshold)
                    rewards = ",".join(map(str, sorted(claimed_list)))
                    uow.viewer_repository.update_session_rewards(
                        session_id=session.id, rewards=rewards, current_time=viewer_time.occurred_at
                    )
                    uow.economy_policy.add_balance(
                        channel_name=viewer_time.channel_name,
                        user_name=session.user_name,
                        amount=reward_amount,
                        transaction_type=TransactionType.VIEWER_TIME_REWARD,
                        description=f"Награда за {minutes_threshold} минут просмотра стрима",
                    )
