from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.chat.domain.repo import ChatRepository
from app.commands.chat.application.chat_message_uow import ChatMessageUnitOfWork, ChatMessageUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.domain.repo import ViewerRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatMessageUnitOfWork(ChatMessageUnitOfWork):
    def __init__(
        self,
        session: Session,
        chat_repo: ChatRepository,
        economy: EconomyPolicy,
        stream_repo: StreamRepository,
        viewer_repo: ViewerRepository,
        conversation_repo: ConversationRepository,
        read_only: bool,
    ):
        self._session = session
        self._chat_repo = chat_repo
        self._economy = economy
        self._stream_repo = stream_repo
        self._viewer_repo = viewer_repo
        self._conversation_repo = conversation_repo
        self._read_only = read_only

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
    def conversation_repo(self) -> ConversationRepository:
        return self._conversation_repo

    def commit(self) -> None:
        if not self._read_only:
            self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class SqlAlchemyChatMessageUnitOfWorkFactory(ChatMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        economy_policy_provider: Provider[EconomyPolicy],
        stream_repo_provider: Provider[StreamRepository],
        viewer_repo_provider: Provider[ViewerRepository],
        conversation_repo_provider: Provider[ConversationRepository],
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._chat_repo_provider = chat_repo_provider
        self._economy_policy_provider = economy_policy_provider
        self._stream_repo_provider = stream_repo_provider
        self._viewer_repo_provider = viewer_repo_provider
        self._conversation_repo_provider = conversation_repo_provider

    def create(self, read_only: bool = False) -> AbstractContextManager[ChatMessageUnitOfWork]:
        session_factory = self._session_factory_ro if read_only else self._session_factory_rw

        @contextmanager
        def _ctx():
            with session_factory() as db:
                uow = SqlAlchemyChatMessageUnitOfWork(
                    session=db,
                    chat_repo=self._chat_repo_provider.get(db),
                    economy=self._economy_policy_provider.get(db),
                    stream_repo=self._stream_repo_provider.get(db),
                    viewer_repo=self._viewer_repo_provider.get(db),
                    conversation_repo=self._conversation_repo_provider.get(db),
                    read_only=read_only,
                )
                try:
                    yield uow
                    if not read_only:
                        uow.commit()
                except Exception:
                    uow.rollback()
                    raise

        return _ctx()
