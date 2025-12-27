from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.twitch.application.interaction.ask.ask_uow import AskUnitOfWork, AskUnitOfWorkFactory, AskUnitOfWorkRo, AskUnitOfWorkRoFactory
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.conversation_service_provider import ConversationServiceProvider


class SqlAlchemyAskUnitOfWork(AskUnitOfWork):

    def __init__(self, chat: ChatUseCase, conversation: ConversationService):
        self._chat = chat
        self._conversation = conversation

    @property
    def chat(self) -> ChatUseCase:
        return self._chat

    @property
    def conversation(self) -> ConversationService:
        return self._conversation


class SqlAlchemyAskUnitOfWorkRo(AskUnitOfWorkRo):
    def __init__(self, conversation: ConversationService):
        self._conversation = conversation

    @property
    def conversation(self) -> ConversationService:
        return self._conversation


class SqlAlchemyAskUnitOfWorkFactory(AskUnitOfWorkFactory):
    def __init__(
        self,
        session_factory: Callable[[], ContextManager[Session]],
        chat_use_case_provider: ChatUseCaseProvider,
        conversation_service_provider: ConversationServiceProvider,
    ):
        self._session_factory = session_factory
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self) -> ContextManager[AskUnitOfWork]:
        @contextmanager
        def _ctx():
            with self._session_factory() as db:
                uow = SqlAlchemyAskUnitOfWork(
                    chat=self._chat_use_case_provider.get(db),
                    conversation=self._conversation_service_provider.get(db),
                )
                yield uow

        return _ctx()


class SqlAlchemyAskUnitOfWorkRoFactory(AskUnitOfWorkRoFactory):
    def __init__(
        self,
        read_session_factory: Callable[[], ContextManager[Session]],
        conversation_service_provider: ConversationServiceProvider,
    ):
        self._read_session_factory = read_session_factory
        self._conversation_service_provider = conversation_service_provider

    def create(self) -> ContextManager[AskUnitOfWorkRo]:
        @contextmanager
        def _ctx():
            with self._read_session_factory() as db:
                uow = SqlAlchemyAskUnitOfWorkRo(
                    conversation=self._conversation_service_provider.get(db),
                )
                yield uow

        return _ctx()
