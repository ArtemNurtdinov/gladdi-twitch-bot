from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.stream.domain.stream_service import StreamService


class ChatSummarizerUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class ChatSummarizerUnitOfWorkFactory(UnitOfWorkFactory[ChatSummarizerUnitOfWork], Protocol):
    pass
