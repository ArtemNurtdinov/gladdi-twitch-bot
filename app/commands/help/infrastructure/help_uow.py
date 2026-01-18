from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.help.application.help_uow import HelpUnitOfWork, HelpUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyHelpUnitOfWork(SqlAlchemyUnitOfWorkBase, HelpUnitOfWork):
    def __init__(self, session: Session, chat_use_case: ChatUseCase, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._chat_use_case = chat_use_case

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyHelpUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[HelpUnitOfWork], HelpUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> HelpUnitOfWork:
        return SqlAlchemyHelpUnitOfWork(
            session=db,
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
