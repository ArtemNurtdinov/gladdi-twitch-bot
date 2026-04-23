from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.platform.chat.application.uow.chat_message_uow import ChatMessageUnitOfWork, ChatMessageUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from app.viewer.session.domain.repository import ViewerRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatMessageUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatMessageUnitOfWork):
    def __init__(
        self,
        session: Session,
        chat_repo: ChatRepository,
        economy: EconomyPolicy,
        stream_repo: StreamRepository,
        viewer_repo: ViewerRepository,
        conversation_service: ConversationService,
        system_prompt_repository: SystemPromptRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._chat_repo = chat_repo
        self._economy = economy
        self._stream_repo = stream_repo
        self._viewer_repo = viewer_repo
        self._conversation_service = conversation_service
        self._system_prompt_repository = system_prompt_repository

    @property
    def chat_repo(self) -> ChatRepository:
        return self._chat_repo

    @property
    def economy(self) -> EconomyPolicy:
        return self._economy

    @property
    def stream_repo(self) -> StreamRepository:
        return self._stream_repo

    @property
    def viewer_repo(self) -> ViewerRepository:
        return self._viewer_repo

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def system_prompt_repository(self) -> SystemPromptRepository:
        return self._system_prompt_repository


class SqlAlchemyChatMessageUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[ChatMessageUnitOfWork], ChatMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider
        self._economy_policy_factory = economy_policy_factory
        self._stream_repository_factory = stream_repository_factory
        self._viewer_repository_factory = viewer_repository_factory
        self._conversation_service_factory = conversation_service_factory
        self._system_prompt_repository_factory = system_prompt_repository_factory

    def _build_uow(self, db: Session, read_only: bool) -> ChatMessageUnitOfWork:
        return SqlAlchemyChatMessageUnitOfWork(
            session=db,
            chat_repo=self._chat_repo_provider.get(db),
            economy=self._economy_policy_factory.get(db),
            stream_repo=self._stream_repository_factory.get(db),
            viewer_repo=self._viewer_repository_factory.get(db),
            conversation_service=self._conversation_service_factory.get(db),
            system_prompt_repository=self._system_prompt_repository_factory.get(db),
            read_only=read_only,
        )
