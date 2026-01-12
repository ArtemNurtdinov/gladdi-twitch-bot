from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository


class FollowAgeUnitOfWork(Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def chat_repo(self) -> ChatRepository: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class FollowAgeUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[FollowAgeUnitOfWork]: ...
