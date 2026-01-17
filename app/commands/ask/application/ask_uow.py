from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class AskUnitOfWork(UnitOfWork, Protocol):
    @property
    def chat_repo(self) -> ChatRepository: ...

    @property
    def conversation_service(self) -> ConversationService: ...


class AskUnitOfWorkFactory(UnitOfWorkFactory[AskUnitOfWork], Protocol):
    pass
