from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.platform.command.followage.application.uow import FollowAgeUnitOfWork, FollowAgeUnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyFollowAgeUnitOfWork(SqlAlchemyUnitOfWorkBase, FollowAgeUnitOfWork):
    def __init__(
        self,
        session: Session,
        conversation_service: ConversationService,
        chat_repository: ChatRepository,
        system_prompt_repository: SystemPromptRepository,
        platform_repository: PlatformRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service
        self._chat_repository = chat_repository
        self._system_prompt_repository = system_prompt_repository
        self._platform_repository = platform_repository

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def chat_repository(self) -> ChatRepository:
        return self._chat_repository

    @property
    def system_prompt_repository(self) -> SystemPromptRepository:
        return self._system_prompt_repository

    @property
    def platform_repository(self) -> PlatformRepository:
        return self._platform_repository


class SqlAlchemyFollowAgeUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[FollowAgeUnitOfWork], FollowAgeUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        platform_repository: PlatformRepository,
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider
        self._conversation_service_factory = conversation_service_factory
        self._system_prompt_repository_factory = system_prompt_repository_factory
        self._platform_repository = platform_repository

    def _build_uow(self, db: Session, read_only: bool) -> FollowAgeUnitOfWork:
        return SqlAlchemyFollowAgeUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_factory.get(db),
            chat_repository=self._chat_repo_provider.get(db),
            system_prompt_repository=self._system_prompt_repository_factory.get(db),
            platform_repository=self._platform_repository,
            read_only=read_only,
        )
