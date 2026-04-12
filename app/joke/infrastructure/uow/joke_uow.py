from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.joke.application.uow.joke_uow import JokeUnitOfWork, JokeUnitOfWorkFactory
from app.joke.domain.repository import JokesConfigurationRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyJokeUnitOfWork(SqlAlchemyUnitOfWorkBase, JokeUnitOfWork):
    def __init__(
        self,
        session: Session,
        conversation_service: ConversationService,
        chat_use_case: ChatUseCase,
        jokes_configuration_repository: JokesConfigurationRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service
        self._chat_use_case = chat_use_case
        self._jokes_configuration_repository = jokes_configuration_repository

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def jokes_configuration_repository(self) -> JokesConfigurationRepository:
        return self._jokes_configuration_repository


class SqlAlchemyJokeUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[JokeUnitOfWork], JokeUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_provider: Provider[ConversationService],
        chat_use_case: ChatUseCase,
        jokes_configuration_repository_provider: Provider[JokesConfigurationRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._conversation_service_provider = conversation_service_provider
        self._chat_use_case = chat_use_case
        self._jokes_configuration_repository_provider = jokes_configuration_repository_provider

    def _build_uow(self, db: Session, read_only: bool) -> JokeUnitOfWork:
        return SqlAlchemyJokeUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_provider.get(db),
            chat_use_case=self._chat_use_case,
            jokes_configuration_repository=self._jokes_configuration_repository_provider.get(db),
            read_only=read_only,
        )
