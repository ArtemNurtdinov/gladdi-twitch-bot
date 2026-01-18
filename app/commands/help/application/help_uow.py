from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class HelpUnitOfWork(UnitOfWork, Protocol):
    @property
    def chat_use_case(self) -> ChatUseCase: ...


class HelpUnitOfWorkFactory(UnitOfWorkFactory[HelpUnitOfWork], Protocol):
    pass
