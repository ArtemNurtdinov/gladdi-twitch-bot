from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.equipment.domain.repo import EquipmentRepository


class EquipmentUseCaseUnitOfWork(UnitOfWork, Protocol):
    @property
    def equipment_repo(self) -> EquipmentRepository: ...


class EquipmentUseCaseUnitOfWorkFactory(UnitOfWorkFactory[EquipmentUseCaseUnitOfWork], Protocol):
    pass
