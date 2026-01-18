from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.top_bottom.application.top_bottom_uow import TopBottomUnitOfWork, TopBottomUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyTopBottomUnitOfWork(SqlAlchemyUnitOfWorkBase, TopBottomUnitOfWork):
    def __init__(self, session: Session, economy_policy: EconomyPolicy, chat_use_case: ChatUseCase, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyTopBottomUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[TopBottomUnitOfWork], TopBottomUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> TopBottomUnitOfWork:
        return SqlAlchemyTopBottomUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
