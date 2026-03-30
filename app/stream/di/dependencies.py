from sqlalchemy.orm import Session

from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.infrastructure.adapter.stream_chat_stats_adapter import StreamChatStatsAdapter
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.core.logger.domain.logger import Logger
from app.minigame.domain.minigame_repository import MinigameRepository
from app.notification.domain.repository import NotificationRepository
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.port.generate_stream_info_port import GenerateStreamInfoPort
from app.stream.application.port.stream_chat_stats_port import StreamChatStatsPort
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.user.application.ports.user_cache_port import UserCachePort


def provide_stream_chat_stats_port(session: Session) -> StreamChatStatsPort:
    return StreamChatStatsAdapter(ChatRepositoryImpl(session))


def provide_handle_stream_status_use_case(
    user_cache: UserCachePort,
    platform_repository: PlatformRepository,
    stream_status_uow_factory: StreamStatusUnitOfWorkFactory,
    minigame_repository: MinigameRepository,
    notification_repository: NotificationRepository,
    notification_group_id: int,
    chat_response_port: GenerateStreamInfoPort,
    state: ChatSummaryState,
    logger: Logger,
) -> HandleStreamStatusUseCase:
    return HandleStreamStatusUseCase(
        user_cache=user_cache,
        platform_repository=platform_repository,
        stream_status_uow=stream_status_uow_factory,
        minigame_repository=minigame_repository,
        notification_repository=notification_repository,
        notification_group_id=notification_group_id,
        chat_response_port=chat_response_port,
        state=state,
        logger=logger,
    )


def provide_stream_status_job(
    channel_name: str,
    handle_stream_status_use_case: HandleStreamStatusUseCase,
) -> StreamStatusJob:
    return StreamStatusJob(channel_name=channel_name, handle_stream_status_use_case=handle_stream_status_use_case)
