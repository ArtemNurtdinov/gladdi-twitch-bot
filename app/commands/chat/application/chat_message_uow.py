from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.domain.repo import ViewerRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class ChatMessageUnitOfWork(UnitOfWork, Protocol):
    @property
    def chat_repo(self) -> ChatRepository: ...

    @property
    def economy(self) -> EconomyPolicy: ...

    @property
    def stream_repo(self) -> StreamRepository: ...

    @property
    def viewer_repo(self) -> ViewerRepository: ...

    @property
    def conversation_service(self) -> ConversationService: ...


class ChatMessageUnitOfWorkFactory(UnitOfWorkFactory[ChatMessageUnitOfWork], Protocol):
    pass
