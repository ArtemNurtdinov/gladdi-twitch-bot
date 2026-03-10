from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.minigame.domain.repo import WordHistoryRepository


class WordHistoryUnitOfWork(UnitOfWork, Protocol):
    @property
    def word_history_repo(self) -> WordHistoryRepository: ...


class WordHistoryUnitOfWorkFactory(UnitOfWorkFactory[WordHistoryUnitOfWork], Protocol):
    pass
