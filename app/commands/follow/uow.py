from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class FollowAgeUnitOfWorkRo(Protocol):
    @property
    def conversation(self) -> ConversationService: ...


class FollowAgeUnitOfWorkRoFactory(Protocol):
    def create(self) -> AbstractContextManager[FollowAgeUnitOfWorkRo]: ...


class FollowAgeUnitOfWorkRw(Protocol):
    @property
    def chat(self) -> ChatUseCase: ...

    @property
    def conversation(self) -> ConversationService: ...


class FollowAgeUnitOfWorkRwFactory(Protocol):
    def create(self) -> AbstractContextManager[FollowAgeUnitOfWorkRw]: ...
