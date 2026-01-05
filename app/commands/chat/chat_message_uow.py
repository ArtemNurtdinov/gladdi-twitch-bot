from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.chat.domain.repo import ChatRepository
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.domain.repo import ViewerRepository


class ChatMessageUnitOfWork(Protocol):
    @property
    def chat_repo(self) -> ChatRepository: ...

    @property
    def economy(self) -> EconomyPolicy: ...

    @property
    def stream_repo(self) -> StreamRepository: ...

    @property
    def viewer_repo(self) -> ViewerRepository: ...

    @property
    def conversation_repo(self) -> ConversationRepository: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class ChatMessageUnitOfWorkFactory(Protocol):
    def create(self, read_only: bool = False) -> AbstractContextManager[ChatMessageUnitOfWork]: ...
