from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.platform.command.ask.application.ask_uow import AskUnitOfWork, AskUnitOfWorkFactory
from core.types import SessionFactory


class SqlAlchemyAskUnitOfWork(SqlAlchemyUnitOfWorkBase, AskUnitOfWork):
    def __init__(
        self,
        session: Session,
        chat_repo: ChatRepository,
        conversation_service: ConversationService,
        system_prompt_repository: SystemPromptRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._chat_repo = chat_repo
        self._conversation_service = conversation_service
        self._system_prompt_repository = system_prompt_repository

    @property
    def chat_repo(self) -> ChatRepository:
        return self._chat_repo

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def system_prompt_repository(self) -> SystemPromptRepository:
        return self._system_prompt_repository


class SqlAlchemyAskUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[AskUnitOfWork], AskUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repository_factory = chat_repository_factory
        self._conversation_service_factory = conversation_service_factory
        self._system_prompt_repository_factory = system_prompt_repository_factory

    def _build_uow(self, db: Session, read_only: bool) -> AskUnitOfWork:
        return SqlAlchemyAskUnitOfWork(
            session=db,
            chat_repo=self._chat_repository_factory.get(db),
            conversation_service=self._conversation_service_factory.get(db),
            system_prompt_repository=self._system_prompt_repository_factory.get(db),
            read_only=read_only,
        )
