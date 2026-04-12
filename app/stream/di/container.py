from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.core.logger.domain.logger import Logger
from app.minigame.domain.minigame_repository import MinigameRepository
from app.notification.domain.repository import NotificationRepository
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from core.db import get_db


class StreamContainer:
    def __init__(self, session: Session):
        self.stream_repository: StreamRepository = StreamRepositoryImpl(session)
        self.chat_repository: ChatRepository = ChatRepositoryImpl(session)
        self.stream_use_case = StreamQueryUseCase(self.stream_repository, self.chat_repository)


def get_stream_container(session: Session = Depends(get_db)) -> StreamContainer:
    return StreamContainer(session)


def get_stream_status_job(
    channel_name: str,
    user_cache: ViewerCachePort,
    platform_repository: PlatformRepository,
    stream_status_uow_factory: StreamStatusUnitOfWorkFactory,
    minigame_repository: MinigameRepository,
    notification_repository: NotificationRepository,
    notification_group_id: int,
    generate_response_use_case: GenerateResponseUseCase,
    state: ChatSummaryState,
    logger: Logger,
) -> StreamStatusJob:
    handle_stream_status_use_case = HandleStreamStatusUseCase(
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
    return StreamStatusJob(channel_name=channel_name, handle_stream_status_use_case=handle_stream_status_use_case, logger=logger)
