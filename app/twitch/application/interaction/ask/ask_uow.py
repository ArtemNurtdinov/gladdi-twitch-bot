from __future__ import annotations

from typing import ContextManager, Protocol

from app.ai.application.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class AskUnitOfWork(Protocol):

    @property
    def chat(self) -> ChatUseCase:
        ...

    @property
    def conversation(self) -> ConversationService:
        ...

class AskUnitOfWorkFactory(Protocol):

    def create(self) -> ContextManager[AskUnitOfWork]:
        ...

