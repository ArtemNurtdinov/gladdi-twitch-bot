from __future__ import annotations

from typing import Protocol

from app.chat.application.chat_use_case import ChatUseCase
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase


class ShopUnitOfWork(UnitOfWork, Protocol):
    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def add_equipment_use_case(self) -> AddEquipmentUseCase: ...

    @property
    def equipment_exists_use_case(self) -> EquipmentExistsUseCase: ...

    @property
    def chat_use_case(self) -> ChatUseCase: ...


class ShopUnitOfWorkFactory(UnitOfWorkFactory[ShopUnitOfWork], Protocol):
    pass
