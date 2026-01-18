from __future__ import annotations

from typing import Protocol

from app.battle.application.battle_use_case import BattleUseCase
from app.betting.application.betting_service import BettingService
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy


class StatsUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def betting_service(self) -> BettingService: ...

    @property
    def battle_use_case(self) -> BattleUseCase: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class StatsUnitOfWorkFactory(UnitOfWorkFactory[StatsUnitOfWork], Protocol):
    pass
