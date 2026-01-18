from __future__ import annotations

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case import BattleUseCase
from app.betting.application.betting_service import BettingService
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.stats.application.stats_uow import StatsUnitOfWork, StatsUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyStatsUnitOfWork(SqlAlchemyUnitOfWorkBase, StatsUnitOfWork):
    def __init__(
        self,
        session: Session,
        economy_policy: EconomyPolicy,
        betting_service: BettingService,
        battle_use_case: BattleUseCase,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._betting_service = betting_service
        self._battle_use_case = battle_use_case
        self._chat_use_case = chat_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def betting_service(self) -> BettingService:
        return self._betting_service

    @property
    def battle_use_case(self) -> BattleUseCase:
        return self._battle_use_case

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyStatsUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[StatsUnitOfWork], StatsUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        betting_service_provider: Provider[BettingService],
        battle_use_case_provider: Provider[BattleUseCase],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._betting_service_provider = betting_service_provider
        self._battle_use_case_provider = battle_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> StatsUnitOfWork:
        return SqlAlchemyStatsUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            betting_service=self._betting_service_provider.get(db),
            battle_use_case=self._battle_use_case_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
