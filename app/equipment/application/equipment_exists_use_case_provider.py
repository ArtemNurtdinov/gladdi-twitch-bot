from typing import Callable

from sqlalchemy.orm import Session

from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase


class EquipmentExistsUseCaseProvider:

    def __init__(self, equipment_exists_use_case: Callable[[Session], EquipmentExistsUseCase]):
        self._equipment_exists_use_case = equipment_exists_use_case

    def get(self, db: Session) -> EquipmentExistsUseCase:
        return self._equipment_exists_use_case(db)
