from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class AskUnitOfWork(Protocol):
    @property
    def chat(self) -> ChatUseCase: ...

    @property
    def conversation(self) -> ConversationService: ...


class AskUnitOfWorkRo(Protocol):
    @property
    def conversation(self) -> ConversationService: ...


class AskUnitOfWorkFactory(Protocol):
    def create(self) -> AbstractContextManager[AskUnitOfWork]: ...


class AskUnitOfWorkRoFactory(Protocol):
    def create(self) -> AbstractContextManager[AskUnitOfWorkRo]: ...
