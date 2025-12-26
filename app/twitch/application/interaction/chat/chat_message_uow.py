from __future__ import annotations

from typing import ContextManager, Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.viewer_session_service import ViewerTimeService


class ChatMessageUnitOfWork(Protocol):

    @property
    def chat(self) -> ChatUseCase:
        ...

    @property
    def economy(self) -> EconomyService:
        ...

    @property
    def stream(self) -> StreamService:
        ...

    @property
    def viewer(self) -> ViewerTimeService:
        ...


class ChatMessageUnitOfWorkFactory(Protocol):

    def create(self) -> ContextManager[ChatMessageUnitOfWork]:
        ...
