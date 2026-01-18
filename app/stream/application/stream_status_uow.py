from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.viewer_session_service import ViewerTimeService


class StreamStatusUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...

    @property
    def start_stream_use_case(self) -> StartNewStreamUseCase: ...

    @property
    def viewer_service(self) -> ViewerTimeService: ...

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
