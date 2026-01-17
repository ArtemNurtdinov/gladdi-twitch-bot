from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.commands.chat.application.chat_message_uow import ChatMessageUnitOfWork, ChatMessageUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.domain.repo import ViewerRepository
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
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._chat_repo = chat_repo
        self._economy = economy
        self._stream_repo = stream_repo
        self._viewer_repo = viewer_repo
        self._conversation_service = conversation_service

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

class SqlAlchemyChatMessageUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[ChatMessageUnitOfWork], ChatMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        economy_policy_provider: Provider[EconomyPolicy],
        stream_repo_provider: Provider[StreamRepository],
        viewer_repo_provider: Provider[ViewerRepository],
        conversation_service_provider: Provider[ConversationService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider
        self._economy_policy_provider = economy_policy_provider
        self._stream_repo_provider = stream_repo_provider
        self._viewer_repo_provider = viewer_repo_provider
        self._conversation_service_provider = conversation_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> ChatMessageUnitOfWork:
        return SqlAlchemyChatMessageUnitOfWork(
            session=db,
            chat_repo=self._chat_repo_provider.get(db),
            economy=self._economy_policy_provider.get(db),
            stream_repo=self._stream_repo_provider.get(db),
            viewer_repo=self._viewer_repo_provider.get(db),
            conversation_service=self._conversation_service_provider.get(db),
            read_only=read_only,
        )
