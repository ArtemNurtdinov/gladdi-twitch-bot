from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository


class AskUnitOfWork(Protocol):
    @property
    def chat_repo(self) -> ChatRepository: ...

    @property
    def conversation_service(self) -> ConversationService: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class AskUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[AskUnitOfWork]: ...
