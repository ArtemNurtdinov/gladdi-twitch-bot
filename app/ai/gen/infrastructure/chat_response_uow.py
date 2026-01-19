from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.application.chat_response_uow import ChatResponseUnitOfWork, ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatResponseUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatResponseUnitOfWork):
    def __init__(self, session: Session, conversation_service: ConversationService, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._conversation_service = conversation_service

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service


class SqlAlchemyChatResponseUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[ChatResponseUnitOfWork], ChatResponseUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        conversation_service_provider: Provider[ConversationService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._conversation_service_provider = conversation_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> ChatResponseUnitOfWork:
        return SqlAlchemyChatResponseUnitOfWork(
            session=db,
            conversation_service=self._conversation_service_provider.get(db),
            read_only=read_only,
        )
