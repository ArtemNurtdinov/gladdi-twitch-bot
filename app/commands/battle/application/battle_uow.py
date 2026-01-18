from __future__ import annotations

from typing import Protocol

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase


class BattleUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...

    @property
    def conversation_service(self) -> ConversationService: ...

    @property
    def battle_use_case(self) -> BattleUseCase: ...

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase: ...


class BattleUnitOfWorkFactory(UnitOfWorkFactory[BattleUnitOfWork], Protocol):
    pass
