from datetime import datetime, timedelta

from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory


class AddEquipmentUseCase:
    _DURATION_DAYS = 90

    def __init__(self, unit_of_work_factory: EquipmentUseCaseUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def add(self, channel_name: str, user_name: str, shop_item_id: int) -> None:
        expires_at = datetime.utcnow() + timedelta(days=self._DURATION_DAYS)

        with self._unit_of_work_factory.create() as uow:
            uow.equipment_repo.add_equipment(
                channel_name=channel_name, user_name=user_name, shop_item_id=shop_item_id, expires_at=expires_at
            )
