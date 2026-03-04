from __future__ import annotations

from typing import Protocol

from app.chat.domain.repo import ChatRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class ChatUseCaseUnitOfWork(UnitOfWork, Protocol):
    @property
    def chat_repo(self) -> ChatRepository: ...


class ChatUseCaseUnitOfWorkFactory(UnitOfWorkFactory[ChatUseCaseUnitOfWork], Protocol):
    pass
