from typing import Protocol, ContextManager

from app.ai.gen.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase


class FollowAgeUnitOfWorkRo(Protocol):

    @property
    def conversation(self) -> ConversationService:
        ...


class FollowAgeUnitOfWorkRoFactory(Protocol):

    def create(self) -> ContextManager[FollowAgeUnitOfWorkRo]:
        ...


class FollowAgeUnitOfWorkRw(Protocol):

    @property
    def chat(self) -> ChatUseCase:
        ...

    @property
    def conversation(self) -> ConversationService:
        ...


class FollowAgeUnitOfWorkRwFactory(Protocol):

    def create(self) -> ContextManager[FollowAgeUnitOfWorkRw]:
        ...
