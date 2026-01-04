from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.chat.chat_message_uow import ChatMessageUnitOfWork, ChatMessageUnitOfWorkFactory
from app.economy.domain.economy_service import EconomyService
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatMessageUnitOfWork(ChatMessageUnitOfWork):
    def __init__(
        self,
        session: Session,
        chat: ChatUseCase,
        economy: EconomyService,
        stream: StreamService,
        viewer: ViewerTimeService,
        conversation: ConversationService,
        read_only: bool,
    ):
        self._session = session
        self._chat = chat
        self._economy = economy
        self._stream = stream
        self._viewer = viewer
        self._conversation = conversation
        self._read_only = read_only

    @property
    def chat(self) -> ChatUseCase:
        return self._chat

    @property
    def economy(self) -> EconomyService:
        return self._economy

    @property
    def stream(self) -> StreamService:
        return self._stream

    @property
    def viewer(self) -> ViewerTimeService:
        return self._viewer

    @property
    def conversation(self) -> ConversationService:
        return self._conversation

    def commit(self) -> None:
        if not self._read_only:
            self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class SqlAlchemyChatMessageUnitOfWorkFactory(ChatMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory: SessionFactory,
        chat_use_case_provider: Provider[ChatUseCase],
        economy_service_provider: Provider[EconomyService],
        stream_service_provider: Provider[StreamService],
        viewer_service_provider: Provider[ViewerTimeService],
        conversation_service_provider: Provider[ConversationService],
    ):
        self._session_factory = session_factory
        self._chat_use_case_provider = chat_use_case_provider
        self._economy_service_provider = economy_service_provider
        self._stream_service_provider = stream_service_provider
        self._viewer_service_provider = viewer_service_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self, read_only: bool = False) -> AbstractContextManager[ChatMessageUnitOfWork]:
        @contextmanager
        def _ctx():
            with self._session_factory() as db:
                uow = SqlAlchemyChatMessageUnitOfWork(
                    session=db,
                    chat=self._chat_use_case_provider.get(db),
                    economy=self._economy_service_provider.get(db),
                    stream=self._stream_service_provider.get(db),
                    viewer=self._viewer_service_provider.get(db),
                    conversation=self._conversation_service_provider.get(db),
                    read_only=read_only,
                )
                try:
                    yield uow
                    uow.commit()
                except Exception:
                    uow.rollback()
                    raise

        return _ctx()
