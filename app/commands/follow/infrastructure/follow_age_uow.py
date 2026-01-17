from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.commands.follow.application.uow import FollowAgeUnitOfWork, FollowAgeUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyFollowAgeUnitOfWork(SqlAlchemyUnitOfWorkBase, FollowAgeUnitOfWork):
    def __init__(
        self,
        session: Session,
        conversation_service: ConversationService,
        chat_repo: ChatRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service
        self._chat_repo = chat_repo

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    @property
    def chat_repo(self) -> ChatRepository:
        return self._chat_repo

class SqlAlchemyFollowAgeUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[FollowAgeUnitOfWork], FollowAgeUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        conversation_service_provider: Provider[ConversationService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider
        self._conversation_service_provider = conversation_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> FollowAgeUnitOfWork:
        return SqlAlchemyFollowAgeUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_provider.get(db),
            chat_repo=self._chat_repo_provider.get(db),
            read_only=read_only,
        )
