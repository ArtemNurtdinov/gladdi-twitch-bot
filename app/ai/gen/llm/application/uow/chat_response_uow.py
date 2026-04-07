from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class ChatResponseUnitOfWork(UnitOfWork, Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def system_prompt_repository(self) -> SystemPromptRepository: ...


class ChatResponseUnitOfWorkFactory(UnitOfWorkFactory[ChatResponseUnitOfWork], Protocol):
    pass
