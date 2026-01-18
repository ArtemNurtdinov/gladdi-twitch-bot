from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy


class GuessUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class GuessUnitOfWorkFactory(UnitOfWorkFactory[GuessUnitOfWork], Protocol):
    pass
