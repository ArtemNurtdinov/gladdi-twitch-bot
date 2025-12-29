from typing import Callable

from sqlalchemy.orm import Session

from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase


class AddEquipmentUseCaseProvider:

    def __init__(self, add_equipment_use_case: Callable[[Session], AddEquipmentUseCase]):
        self._add_equipment_use_case = add_equipment_use_case

    def get(self, db: Session) -> AddEquipmentUseCase:
        return self._add_equipment_use_case(db)
