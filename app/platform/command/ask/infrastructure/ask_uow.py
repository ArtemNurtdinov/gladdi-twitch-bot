from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.platform.command.ask.application.ask_uow import AskUnitOfWork, AskUnitOfWorkFactory
from core.provider import Provider
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
        chat_repo_provider: Provider[ChatRepository],
        conversation_service_provider: Provider[ConversationService],
        system_prompt_repository_provider: Provider[SystemPromptRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider
        self._conversation_service_provider = conversation_service_provider
        self._system_prompt_repository_provider = system_prompt_repository_provider

    def _build_uow(self, db: Session, read_only: bool) -> AskUnitOfWork:
        return SqlAlchemyAskUnitOfWork(
            session=db,
            chat_repo=self._chat_repo_provider.get(db),
            conversation_service=self._conversation_service_provider.get(db),
            system_prompt_repository=self._system_prompt_repository_provider.get(db),
            read_only=read_only,
        )
