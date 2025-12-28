from typing import Callable

from sqlalchemy.orm import Session

from app.equipment.domain.equipment_service import EquipmentService


class EquipmentServiceProvider:

    def __init__(self, equipment_service_factory: Callable[[Session], EquipmentService]):
        self._equipment_service_factory = equipment_service_factory

    def get(self, db: Session) -> EquipmentService:
        return self._equipment_service_factory(db)
