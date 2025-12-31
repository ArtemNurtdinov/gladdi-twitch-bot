from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.gen.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.ask.ask_uow import AskUnitOfWorkRo
from app.commands.follow.uow import FollowAgeUnitOfWorkRo, FollowAgeUnitOfWorkRoFactory, FollowAgeUnitOfWorkRw, \
    FollowAgeUnitOfWorkRwFactory
from core.provider import Provider


class SqlAlchemyFollowAgeUnitOfWorkRo(FollowAgeUnitOfWorkRo):

    def __init__(self, conversation: ConversationService):
        self._conversation = conversation

    @property
    def conversation(self) -> ConversationService:
        return self._conversation


class SqlAlchemyFollowAgeUnitOfWorkRoFactory(FollowAgeUnitOfWorkRoFactory):

    def __init__(
        self,
        read_session_factory: Callable[[], ContextManager[Session]],
        conversation_service_provider: Provider[ConversationService],
    ):
        self._read_session_factory = read_session_factory
        self._conversation_service_provider = conversation_service_provider

    def create(self) -> ContextManager[AskUnitOfWorkRo]:
        @contextmanager
        def _ctx():
            with self._read_session_factory() as db:
                uow = SqlAlchemyFollowAgeUnitOfWorkRo(
                    conversation=self._conversation_service_provider.get(db),
                )
                yield uow

        return _ctx()


class SqlAlchemyFollowAgeUnitOfWorkRw(FollowAgeUnitOfWorkRw):

    def __init__(self, chat_use_case: ChatUseCase, conversation: ConversationService):
        self._chat_use_case = chat_use_case
        self._conversation = conversation

    @property
    def chat(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def conversation(self) -> ConversationService:
        return self._conversation


class SqlAlchemyFollowAgeUnitOfWorkRwFactory(FollowAgeUnitOfWorkRwFactory):

    def __init__(
        self,
        session_factory: Callable[[], ContextManager[Session]],
        chat_use_case_provider: Provider[ChatUseCase],
        conversation_service_provider: Provider[ConversationService],
    ):
        self._session_factory = session_factory
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self) -> ContextManager[FollowAgeUnitOfWorkRw]:
        @contextmanager
        def _ctx():
            with self._session_factory() as db:
                uow = SqlAlchemyFollowAgeUnitOfWorkRw(
                    chat_use_case=self._chat_use_case_provider.get(db),
                    conversation=self._conversation_service_provider.get(db),
                )
                yield uow

        return _ctx()
