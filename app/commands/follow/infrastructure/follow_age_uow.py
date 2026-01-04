from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.follow.uow import FollowAgeUnitOfWork, FollowAgeUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyFollowAgeUnitOfWork(FollowAgeUnitOfWork):
    def __init__(self, session: Session, conversation: ConversationService, chat_use_case: ChatUseCase, read_only: bool):
        self._session = session
        self._conversation = conversation
        self._chat_use_case = chat_use_case
        self._read_only = read_only

    @property
    def conversation(self) -> ConversationService:
        return self._conversation

    @property
    def chat(self) -> ChatUseCase:
        return self._chat_use_case

    def commit(self) -> None:
        if not self._read_only:
            self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class SqlAlchemyFollowAgeUnitOfWorkFactory(FollowAgeUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_use_case_provider: Provider[ChatUseCase],
        conversation_service_provider: Provider[ConversationService],
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self, read_only: bool = False) -> AbstractContextManager[FollowAgeUnitOfWork]:
        session_factory = self._session_factory_ro if read_only else self._session_factory_rw

        @contextmanager
        def _ctx():
            with session_factory() as db:
                uow = SqlAlchemyFollowAgeUnitOfWork(
                    session=db,
                    conversation=self._conversation_service_provider.get(db),
                    chat_use_case=self._chat_use_case_provider.get(db),
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
