from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.stream.domain.stream_service import StreamService
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.economy_service_provider import EconomyServiceProvider
from app.twitch.application.shared.stream_service_provider import StreamServiceProvider
from app.twitch.application.interaction.chat.chat_message_uow import ChatMessageUnitOfWork, ChatMessageUnitOfWorkFactory
from app.twitch.application.shared.viewer_service_provider import ViewerServiceProvider
from app.twitch.application.shared.conversation_service_provider import ConversationServiceProvider
from app.viewer.domain.viewer_session_service import ViewerTimeService


class SqlAlchemyChatMessageUnitOfWork(ChatMessageUnitOfWork):

    def __init__(
        self,
        chat: ChatUseCase,
        economy: EconomyService,
        stream: StreamService,
        viewer: ViewerTimeService,
        conversation: ConversationService,
    ):
        self._chat = chat
        self._economy = economy
        self._stream = stream
        self._viewer = viewer
        self._conversation = conversation

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


class SqlAlchemyChatMessageUnitOfWorkFactory(ChatMessageUnitOfWorkFactory):
    def __init__(
        self,
        session_factory: Callable[[], ContextManager[Session]],
        chat_use_case_provider: ChatUseCaseProvider,
        economy_service_provider: EconomyServiceProvider,
        stream_service_provider: StreamServiceProvider,
        viewer_service_provider: ViewerServiceProvider,
        conversation_service_provider: ConversationServiceProvider,
    ):
        self._session_factory = session_factory
        self._chat_use_case_provider = chat_use_case_provider
        self._economy_service_provider = economy_service_provider
        self._stream_service_provider = stream_service_provider
        self._viewer_service_provider = viewer_service_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self) -> ContextManager[ChatMessageUnitOfWork]:
        @contextmanager
        def _ctx():
            with self._session_factory() as db:
                uow = SqlAlchemyChatMessageUnitOfWork(
                    chat=self._chat_use_case_provider.get(db),
                    economy=self._economy_service_provider.get(db),
                    stream=self._stream_service_provider.get(db),
                    viewer=self._viewer_service_provider.get(db),
                    conversation=self._conversation_service_provider.get(db),
                )
                yield uow

        return _ctx()
