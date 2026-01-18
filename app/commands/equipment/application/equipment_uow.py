from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase


class EquipmentUnitOfWork(UnitOfWork, Protocol):
    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class EquipmentUnitOfWorkFactory(UnitOfWorkFactory[EquipmentUnitOfWork], Protocol):
    pass
