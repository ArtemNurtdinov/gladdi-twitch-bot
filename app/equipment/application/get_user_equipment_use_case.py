from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory
from app.equipment.domain.models import UserEquipmentItem


class GetUserEquipmentUseCase:
    def __init__(self, unit_of_work_factory: EquipmentUseCaseUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def get_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return uow.equipment_repo.list_user_equipment(channel_name, user_name)
