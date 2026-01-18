from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.stream.domain.stream_service import StreamService


class BonusUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase: ...

    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class BonusUnitOfWorkFactory(UnitOfWorkFactory[BonusUnitOfWork], Protocol):
    pass
