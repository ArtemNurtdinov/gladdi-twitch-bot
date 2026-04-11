from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.core.logger.domain.logger import Logger
from app.minigame.domain.minigame_repository import MinigameRepository
from app.notification.domain.repository import NotificationRepository
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.viewer.application.port.viewer_cache_port import ViewerCachePort


def provide_handle_stream_status_use_case(
    user_cache: ViewerCachePort,
    platform_repository: PlatformRepository,
    stream_status_uow_factory: StreamStatusUnitOfWorkFactory,
    minigame_repository: MinigameRepository,
    notification_repository: NotificationRepository,
    notification_group_id: int,
    generate_response_use_case: GenerateResponseUseCase,
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
        generate_response_use_case=generate_response_use_case,
        state=state,
        logger=logger,
    )


def provide_stream_status_job(
    channel_name: str, handle_stream_status_use_case: HandleStreamStatusUseCase, logger: Logger
) -> StreamStatusJob:
    return StreamStatusJob(channel_name=channel_name, handle_stream_status_use_case=handle_stream_status_use_case, logger=logger)
