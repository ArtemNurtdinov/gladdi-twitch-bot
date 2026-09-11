from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.periodic_message.domain.repository import PeriodicMessageRepository
from app.stream.domain.repo import StreamRepository


class PeriodicMessageUnitOfWork(UnitOfWork, Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...

    @property
    def periodic_message_repository(self) -> PeriodicMessageRepository: ...

    @property
    def stream_repository(self) -> StreamRepository: ...


class PeriodicMessageUnitOfWorkFactory(UnitOfWorkFactory[PeriodicMessageUnitOfWork], Protocol):
    pass
