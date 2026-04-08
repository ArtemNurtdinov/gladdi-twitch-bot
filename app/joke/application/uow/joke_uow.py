from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.joke.domain.repository import JokesConfigurationRepository


class JokeUnitOfWork(UnitOfWork, Protocol):
    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...

    @property
    def jokes_configuration_repository(self) -> JokesConfigurationRepository: ...


class JokeUnitOfWorkFactory(UnitOfWorkFactory[JokeUnitOfWork], Protocol):
    pass
