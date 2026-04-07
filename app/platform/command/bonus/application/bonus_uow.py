from __future__ import annotations

from typing import Protocol

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.stream.domain.repo import StreamRepository


class BonusUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_repository(self) -> StreamRepository: ...

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase: ...

    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class BonusUnitOfWorkFactory(UnitOfWorkFactory[BonusUnitOfWork], Protocol):
    pass
