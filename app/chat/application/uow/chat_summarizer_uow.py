from __future__ import annotations

from typing import Protocol

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.stream.domain.repo import StreamRepository


class ChatSummarizerUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_repository(self) -> StreamRepository: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class ChatSummarizerUnitOfWorkFactory(UnitOfWorkFactory[ChatSummarizerUnitOfWork], Protocol):
    pass
