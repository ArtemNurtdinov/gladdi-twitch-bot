from __future__ import annotations

from typing import Protocol

from app.battle.domain.repo import BattleRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class BattleUseCaseUnitOfWork(UnitOfWork, Protocol):
    @property
    def battle_repo(self) -> BattleRepository: ...


class BattleUseCaseUnitOfWorkFactory(UnitOfWorkFactory[BattleUseCaseUnitOfWork], Protocol):
    pass
