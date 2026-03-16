from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.repo import ViewerRepository


class StreamStatusUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...

    @property
    def stream_repository(self) -> StreamRepository: ...

    @property
    def viewer_repository(self) -> ViewerRepository: ...

    @property
    def battle_use_case(self) -> BattleUseCase: ...

    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...

    @property
    def conversation_service(self) -> ConversationService: ...


class StreamStatusUnitOfWorkFactory(UnitOfWorkFactory[StreamStatusUnitOfWork], Protocol):
    pass
