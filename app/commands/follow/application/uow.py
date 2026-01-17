from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.domain.repo import ChatRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class FollowAgeUnitOfWork(UnitOfWork, Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def chat_repo(self) -> ChatRepository: ...


class FollowAgeUnitOfWorkFactory(UnitOfWorkFactory[FollowAgeUnitOfWork], Protocol):
    pass
