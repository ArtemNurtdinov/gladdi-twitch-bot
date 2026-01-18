from __future__ import annotations

from typing import Protocol

from app.betting.application.betting_service import BettingService
from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase


class RollUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def betting_service(self) -> BettingService: ...

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class RollUnitOfWorkFactory(UnitOfWorkFactory[RollUnitOfWork], Protocol):
    pass
