from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.infrastructure.db.session_scoped_factory import SessionScopedFactory
from app.common.infrastructure.db.types import SessionFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.periodic_message.application.uow.periodic_message_uow import PeriodicMessageUnitOfWork, PeriodicMessageUnitOfWorkFactory
from app.periodic_message.domain.repository import PeriodicMessageRepository
from app.stream.domain.repo import StreamRepository


class SqlAlchemyPeriodicMessageUnitOfWork(SqlAlchemyUnitOfWorkBase, PeriodicMessageUnitOfWork):
    def __init__(
        self,
        session: Session,
        conversation_service: ConversationService,
        chat_use_case: ChatUseCase,
        periodic_message_repository: PeriodicMessageRepository,
        stream_repository: StreamRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service
        self._chat_use_case = chat_use_case
        self._periodic_message_repository = periodic_message_repository
        self._stream_repository = stream_repository

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def periodic_message_repository(self) -> PeriodicMessageRepository:
        return self._periodic_message_repository

    @property
    def stream_repository(self) -> StreamRepository:
        return self._stream_repository


class SqlAlchemyPeriodicMessageUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[PeriodicMessageUnitOfWork], PeriodicMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        chat_use_case: ChatUseCase,
        periodic_message_repository_factory: SessionScopedFactory[PeriodicMessageRepository],
        stream_repository_factory: SessionScopedFactory[StreamRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._conversation_service_factory = conversation_service_factory
        self._chat_use_case = chat_use_case
        self._periodic_message_repository_factory = periodic_message_repository_factory
        self._stream_repository_factory = stream_repository_factory

    def _build_uow(self, db: Session, read_only: bool) -> PeriodicMessageUnitOfWork:
        return SqlAlchemyPeriodicMessageUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_factory.get(db),
            chat_use_case=self._chat_use_case,
            periodic_message_repository=self._periodic_message_repository_factory.get(db),
            stream_repository=self._stream_repository_factory.get(db),
            read_only=read_only,
        )
