from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class FollowAgeUnitOfWork(Protocol):
    @property
    def conversation(self) -> ConversationService: ...

    @property
    def chat(self) -> ChatUseCase: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class FollowAgeUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[FollowAgeUnitOfWork]: ...
