from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.logger.domain.logger import Logger
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationDTOMapper
from app.joke.application.uow.joke_uow import JokeUnitOfWorkFactory
from app.joke.application.usecase.get_jokes_configuration_use_case import GetJokesConfigurationUseCase
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.usecase.save_jokes_configuration_use_case import SaveJokesConfigurationUseCase
from app.joke.domain.repository import JokesConfigurationRepository
from app.joke.infrastructure.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationDbMapper
from app.joke.infrastructure.repository import JokesConfigurationRepositoryImpl
from app.joke.infrastructure.uow.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.joke.presentation.api.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationSchemaMapper
from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from core.types import SessionFactory


class JokeContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, logger: Logger):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.jokes_configuration_db_mapper = JokesConfigurationDbMapper()
        self.jokes_configuration_dto_mapper = JokesConfigurationDTOMapper()
        self.jokes_configuration_schema_mapper = JokesConfigurationSchemaMapper()
        self.logger = logger.create_child(__name__)

    def _jokes_configuration_repository(self, session: Session) -> JokesConfigurationRepository:
        return JokesConfigurationRepositoryImpl(session, self.jokes_configuration_db_mapper)

    def get_jokes_configuration_use_case(self, session: Session) -> GetJokesConfigurationUseCase:
        jokes_configuration_repository = self._jokes_configuration_repository(session)
        return GetJokesConfigurationUseCase(jokes_configuration_repository, self.jokes_configuration_dto_mapper)

    def save_jokes_configuration_use_case(self, session: Session) -> SaveJokesConfigurationUseCase:
        jokes_configuration_repository = self._jokes_configuration_repository(session)
        return SaveJokesConfigurationUseCase(jokes_configuration_repository, self.jokes_configuration_dto_mapper)

    def joke_uow_factory(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        chat_use_case: ChatUseCase,
    ) -> JokeUnitOfWorkFactory:
        return SqlAlchemyJokeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            conversation_service_factory=conversation_service_factory,
            chat_use_case=chat_use_case,
            jokes_configuration_repository_factory=SessionScopedFactory(self._jokes_configuration_repository),
        )

    def handle_post_joke_use_case(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        chat_use_case: ChatUseCase,
        user_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
    ) -> HandlePostJokeUseCase:
        joke_uow_factory = self.joke_uow_factory(session_factory_rw, session_factory_ro, conversation_service_factory, chat_use_case)
        return HandlePostJokeUseCase(
            user_cache=user_cache,
            platform_repository=platform_repository,
            generate_response_use_case_factory=generate_response_use_case_factory,
            joke_uow=joke_uow_factory,
            db_ro_session=self._session_factory_ro,
        )

    def post_joke_job(
        self,
        send_channel_message: Callable[[str], Awaitable[None]],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        chat_use_case: ChatUseCase,
        user_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
    ) -> PostJokeJob:
        handle_post_joke_use_case = self.handle_post_joke_use_case(
            self._session_factory_rw,
            self._session_factory_ro,
            conversation_service_factory,
            chat_use_case,
            user_cache,
            platform_repository,
            generate_response_use_case_factory,
        )
        return PostJokeJob(
            handle_post_joke_use_case=handle_post_joke_use_case,
            send_channel_message=send_channel_message,
            logger=self.logger,
        )
