from collections.abc import Awaitable, Callable

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.core.logger.domain.logger import Logger
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.uow.joke_uow import JokeUnitOfWorkFactory
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.usecase.joke_use_case import JokeUseCase
from app.joke.domain.joke_service import JokeService
from app.joke.domain.repo import JokeSettingsRepository
from app.joke.infrastructure.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.joke.infrastructure.settings_repository import FileJokeSettingsRepository
from app.platform.domain.repository import PlatformRepository
from app.user.application.ports.user_cache_port import UserCachePort
from core.provider import Provider
from core.types import SessionFactory


def provide_joke_settings_repository(logger: Logger) -> JokeSettingsRepository:
    return FileJokeSettingsRepository(logger)


def provide_joke_service(joke_settings_repository: JokeSettingsRepository, logger: Logger) -> JokeService:
    return JokeService(joke_settings_repository, logger)


def provide_joke_unit_of_work_factory(
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    conversation_service_provider: Provider[ConversationService],
    chat_use_case_provider: Provider[ChatUseCase],
) -> JokeUnitOfWorkFactory:
    return SqlAlchemyJokeUnitOfWorkFactory(
        session_factory_rw=session_factory_rw,
        session_factory_ro=session_factory_ro,
        conversation_service_provider=conversation_service_provider,
        chat_use_case_provider=chat_use_case_provider,
    )


def provide_handle_post_joke_use_case(
    joke_service: JokeService,
    user_cache: UserCachePort,
    platform_repository: PlatformRepository,
    generate_response_use_case: GenerateResponseUseCase,
    joke_uow_factory: JokeUnitOfWorkFactory,
) -> HandlePostJokeUseCase:
    return HandlePostJokeUseCase(
        joke_service=joke_service,
        user_cache=user_cache,
        platform_repository=platform_repository,
        chat_response_use_case=generate_response_use_case,
        unit_of_work_factory=joke_uow_factory,
    )


def provide_joke_use_case(joke_service: JokeService) -> JokeUseCase:
    return JokeUseCase(joke_service)


def provide_post_joke_job(
    channel_name: str,
    handle_post_joke_use_case: HandlePostJokeUseCase,
    send_channel_message: Callable[[str], Awaitable[None]],
    bot_name: str,
    logger: Logger,
) -> PostJokeJob:
    return PostJokeJob(
        channel_name=channel_name,
        handle_post_joke_use_case=handle_post_joke_use_case,
        send_channel_message=send_channel_message,
        bot_name=bot_name,
        logger=logger,
    )
