from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class AskUnitOfWork(Protocol):
    @property
    def chat(self) -> ChatUseCase: ...

    @property
    def conversation(self) -> ConversationService: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class AskUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[AskUnitOfWork]: ...
