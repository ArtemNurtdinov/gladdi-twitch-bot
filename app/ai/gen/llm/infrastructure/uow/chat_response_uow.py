from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.uow.chat_response_uow import ChatResponseUnitOfWork, ChatResponseUnitOfWorkFactory
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from core.types import SessionFactory


class SqlAlchemyChatResponseUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatResponseUnitOfWork):
    def __init__(
        self, session: Session, conversation_service: ConversationService, system_prompt_repository: SystemPromptRepository, read_only: bool
    ):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service
        self._system_prompt_repository = system_prompt_repository

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def system_prompt_repository(self) -> SystemPromptRepository:
        return self._system_prompt_repository


class SqlAlchemyChatResponseUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[ChatResponseUnitOfWork], ChatResponseUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._conversation_service_factory = conversation_service_factory
        self._system_prompt_repository_factory = system_prompt_repository_factory

    def _build_uow(self, db: Session, read_only: bool) -> ChatResponseUnitOfWork:
        return SqlAlchemyChatResponseUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_factory.get(db),
            system_prompt_repository=self._system_prompt_repository_factory.get(db),
            read_only=read_only,
        )
