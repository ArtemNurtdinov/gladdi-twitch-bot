from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class JokeUnitOfWork(UnitOfWork, Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class JokeUnitOfWorkFactory(UnitOfWorkFactory[JokeUnitOfWork], Protocol):
    pass
