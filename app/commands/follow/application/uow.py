from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.chat.domain.repo import ChatRepository


class FollowAgeUnitOfWork(Protocol):
    @property
    def conversation_repo(self) -> ConversationRepository: ...

    @property
    def chat_repo(self) -> ChatRepository: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class FollowAgeUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[FollowAgeUnitOfWork]: ...
