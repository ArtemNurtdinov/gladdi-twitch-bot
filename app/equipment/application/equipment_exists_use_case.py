from app.economy.domain.models import ShopItemType
from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory


class EquipmentExistsUseCase:
    def __init__(self, unit_of_work_factory: EquipmentUseCaseUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def check_equipment_exists(self, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return uow.equipment_repo.equipment_exists(channel_name, user_name, item_type)
