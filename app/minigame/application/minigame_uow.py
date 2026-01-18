from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.minigame.application.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.get_used_words_use_case import GetUsedWordsUseCase
from app.stream.domain.stream_service import StreamService


class MinigameUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...

    @property
    def stream_service(self) -> StreamService: ...

    @property
    def get_used_words_use_case(self) -> GetUsedWordsUseCase: ...

    @property
    def add_used_words_use_case(self) -> AddUsedWordsUseCase: ...

    @property
    def conversation_service(self) -> ConversationService: ...


class MinigameUnitOfWorkFactory(UnitOfWorkFactory[MinigameUnitOfWork], Protocol):
    pass
