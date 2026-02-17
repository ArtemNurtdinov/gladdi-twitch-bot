from app.economy.domain.models import TransactionType
from app.user.application.ports.user_cache_port import UserCachePort
from app.viewer.application.model import ViewerTimeDTO
from app.viewer.application.stream_chatters_port import StreamChattersPort
from app.viewer.application.viewer_time_uow import ViewerTimeUnitOfWorkFactory


class HandleViewerTimeUseCase:
    def __init__(
        self,
        unit_of_work_factory: ViewerTimeUnitOfWorkFactory,
        user_cache: UserCachePort,
        stream_chatters_port: StreamChattersPort,
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._user_cache = user_cache
        self._stream_chatters_port = stream_chatters_port

    async def handle(
        self,
        viewer_time_dto: ViewerTimeDTO,
    ):
        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(viewer_time_dto.channel_name)

        if not active_stream:
            return

        with self._unit_of_work_factory.create() as uow:
            uow.viewer_service.check_inactive_viewers(active_stream.id, viewer_time_dto.occurred_at)

        broadcaster_id = await self._user_cache.get_user_id(viewer_time_dto.channel_name)
        moderator_id = await self._user_cache.get_user_id(viewer_time_dto.bot_nick or viewer_time_dto.channel_name)
        chatters = await self._stream_chatters_port.get_stream_chatters(broadcaster_id, moderator_id)
        if chatters:
            with self._unit_of_work_factory.create() as uow:
                uow.viewer_service.update_viewers(
                    active_stream_id=active_stream.id,
                    channel_name=viewer_time_dto.channel_name,
                    chatters=chatters,
                    current_time=viewer_time_dto.occurred_at,
                )

        with self._unit_of_work_factory.create(read_only=True) as uow:
            viewers_count = uow.viewer_service.get_stream_watchers_count(active_stream.id)

        if viewers_count > active_stream.max_concurrent_viewers:
            with self._unit_of_work_factory.create() as uow:
                uow.stream_service.update_max_concurrent_viewers_count(active_stream.id, viewers_count)

        with self._unit_of_work_factory.create() as uow:
            viewer_sessions = uow.viewer_service.get_stream_viewer_sessions(active_stream.id)
            for session in viewer_sessions:
                available_rewards = uow.viewer_service.get_available_rewards(session)
                for minutes_threshold, reward_amount in available_rewards:
                    claimed_list = session.get_claimed_rewards_list()
                    claimed_list.append(minutes_threshold)
                    rewards = ",".join(map(str, sorted(claimed_list)))
                    uow.viewer_service.update_session_rewards(
                        session_id=session.id, rewards=rewards, current_time=viewer_time_dto.occurred_at
                    )
                    uow.economy_policy.add_balance(
                        channel_name=viewer_time_dto.channel_name,
                        user_name=session.user_name,
                        amount=reward_amount,
                        transaction_type=TransactionType.VIEWER_TIME_REWARD,
                        description=f"Награда за {minutes_threshold} минут просмотра стрима",
                    )
