from typing import Callable

from sqlalchemy.orm import Session

from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase


class GetUserEquipmentUseCaseProvider:

    def __init__(self, get_user_equipment_use_case_factory: Callable[[Session], GetUserEquipmentUseCase]):
        self._get_user_equipment_use_case_factory = get_user_equipment_use_case_factory

    def get(self, db: Session) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case_factory(db)
