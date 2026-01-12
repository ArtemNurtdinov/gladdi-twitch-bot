from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.commands.ask.application.ask_uow import AskUnitOfWork, AskUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyAskUnitOfWork(AskUnitOfWork):
    def __init__(self, session: Session, chat_repo: ChatRepository, conversation_service: ConversationService, read_only: bool):
        self._session = session
        self._chat_repo = chat_repo
        self._conversation_service = conversation_service
        self._read_only = read_only

    @property
    def chat_repo(self) -> ChatRepository:
        return self._chat_repo

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service

    def commit(self) -> None:
        if not self._read_only:
            self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class SqlAlchemyAskUnitOfWorkFactory(AskUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
        conversation_service_provider: Provider[ConversationService],
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._chat_repo_provider = chat_repo_provider
        self._conversation_service_provider = conversation_service_provider

    def create(self, read_only: bool = False) -> AbstractContextManager[AskUnitOfWork]:
        session_factory = self._session_factory_ro if read_only else self._session_factory_rw

        @contextmanager
        def _ctx():
            with session_factory() as db:
                uow = SqlAlchemyAskUnitOfWork(
                    session=db,
                    chat_repo=self._chat_repo_provider.get(db),
                    conversation_service=self._conversation_service_provider.get(db),
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
