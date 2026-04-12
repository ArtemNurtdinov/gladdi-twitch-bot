from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.core.logger.domain.logger import Logger
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationMapperDTO
from app.joke.application.uow.joke_uow import JokeUnitOfWorkFactory
from app.joke.application.usecase.get_jokes_configuration_use_case import GetJokesConfigurationUseCase
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.usecase.save_jokes_configuration_use_case import SaveJokesConfigurationUseCase
from app.joke.domain.repository import JokesConfigurationRepository
from app.joke.infrastructure.mapper.jokes_configuration_mapper import JokesConfigurationMapper
from app.joke.infrastructure.repository import JokesConfigurationRepositoryImpl
from app.joke.infrastructure.uow.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.joke.presentation.api.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationMapperSchema
from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from core.provider import Provider
from core.types import SessionFactory


def provide_joke_unit_of_work_factory(
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    conversation_service_provider: Provider[ConversationService],
    chat_use_case: ChatUseCase,
    jokes_configuration_repository_provider: Provider[JokesConfigurationRepository],
) -> JokeUnitOfWorkFactory:
    return SqlAlchemyJokeUnitOfWorkFactory(
        session_factory_rw=session_factory_rw,
        session_factory_ro=session_factory_ro,
        conversation_service_provider=conversation_service_provider,
        chat_use_case=chat_use_case,
        jokes_configuration_repository_provider=jokes_configuration_repository_provider,
    )


def provide_handle_post_joke_use_case(
    user_cache: ViewerCachePort,
    platform_repository: PlatformRepository,
    generate_response_use_case: GenerateResponseUseCase,
    joke_uow_factory: JokeUnitOfWorkFactory,
) -> HandlePostJokeUseCase:
    return HandlePostJokeUseCase(
        user_cache=user_cache,
        platform_repository=platform_repository,
        chat_response_use_case=generate_response_use_case,
        joke_uow=joke_uow_factory,
    )


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


def provide_jokes_configuration_mapper() -> JokesConfigurationMapper:
    return JokesConfigurationMapper()


def provide_jokes_configuration_mapper_dto() -> JokesConfigurationMapperDTO:
    return JokesConfigurationMapperDTO()


def provide_jokes_configuration_repository(session: Session, mapper: JokesConfigurationMapper) -> JokesConfigurationRepository:
    return JokesConfigurationRepositoryImpl(session, mapper)


def provide_get_jokes_configuration_use_case(
    jokes_configuration_repository: JokesConfigurationRepository, mapper: JokesConfigurationMapperDTO
) -> GetJokesConfigurationUseCase:
    return GetJokesConfigurationUseCase(jokes_configuration_repository, mapper)


def provide_save_jokes_configuration_use_case(
    jokes_configuration_repository: JokesConfigurationRepository, mapper: JokesConfigurationMapperDTO
) -> SaveJokesConfigurationUseCase:
    return SaveJokesConfigurationUseCase(jokes_configuration_repository, mapper)


def provide_jokes_configuration_mapper_schema() -> JokesConfigurationMapperSchema:
    return JokesConfigurationMapperSchema()
