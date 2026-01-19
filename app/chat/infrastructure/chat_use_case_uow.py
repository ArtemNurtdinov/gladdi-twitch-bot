from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case_uow import ChatUseCaseUnitOfWork, ChatUseCaseUnitOfWorkFactory
from app.chat.domain.repo import ChatRepository
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatUseCaseUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatUseCaseUnitOfWork):
    def __init__(self, session: Session, chat_repo: ChatRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._chat_repo = chat_repo

    @property
    def chat_repo(self) -> ChatRepository:
        return self._chat_repo


class SqlAlchemyChatUseCaseUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[ChatUseCaseUnitOfWork], ChatUseCaseUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_repo_provider: Provider[ChatRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_repo_provider = chat_repo_provider

    def _build_uow(self, db: Session, read_only: bool) -> ChatUseCaseUnitOfWork:
        return SqlAlchemyChatUseCaseUnitOfWork(
            session=db,
            chat_repo=self._chat_repo_provider.get(db),
            read_only=read_only,
        )
