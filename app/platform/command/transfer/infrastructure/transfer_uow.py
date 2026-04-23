from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.platform.command.transfer.application.transfer_uow import TransferUnitOfWork, TransferUnitOfWorkFactory
from core.types import SessionFactory


class SqlAlchemyTransferUnitOfWork(SqlAlchemyUnitOfWorkBase, TransferUnitOfWork):
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


class SqlAlchemyTransferUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[TransferUnitOfWork], TransferUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_factory = economy_policy_factory
        self._chat_use_case = chat_use_case

    def _build_uow(self, db: Session, read_only: bool) -> TransferUnitOfWork:
        return SqlAlchemyTransferUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_factory.get(db),
            chat_use_case=self._chat_use_case,
            read_only=read_only,
        )
