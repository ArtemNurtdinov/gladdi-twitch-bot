from sqlalchemy.orm import Session

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.domain.repo import EconomyRepository
from app.economy.infrastructure.economy_repository import EconomyRepositoryImpl
from app.platform.command.balance.application.balance_uow import BalanceUnitOfWorkFactory
from app.platform.command.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.platform.command.balance.infrastructure.balance_uow import SqlAlchemyBalanceUnitOfWorkFactory
from core.types import SessionFactory


class EconomyContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.economy_policy_factory: SessionScopedFactory[EconomyPolicy] = SessionScopedFactory(self.economy_policy)

    def economy_repository(self, session: Session) -> EconomyRepository:
        return EconomyRepositoryImpl(session)

    def economy_policy(self, session: Session) -> EconomyPolicy:
        economy_repository = self.economy_repository(session)
        return EconomyPolicy(economy_repository)

    def balance_uow_factory(self, chat_use_case: ChatUseCase) -> BalanceUnitOfWorkFactory:
        return SqlAlchemyBalanceUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            economy_policy_factory=self.economy_policy_factory,
            chat_use_case=chat_use_case,
        )

    def handle_balance_use_case(self, chat_use_case: ChatUseCase) -> HandleBalanceUseCase:
        balance_uow_factory = self.balance_uow_factory(chat_use_case)
        return HandleBalanceUseCase(balance_uow_factory)
