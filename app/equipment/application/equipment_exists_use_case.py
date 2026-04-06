from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory


class EquipmentExistsUseCase:
    def __init__(self, equipment_uow: EquipmentUseCaseUnitOfWorkFactory):
        self._equipment_uow = equipment_uow

    def check_equipment_exists(self, channel_name: str, user_name: str, shop_item_id: int) -> bool:
        with self._equipment_uow.create(read_only=True) as uow:
            return uow.equipment_repo.equipment_exists(channel_name, user_name, shop_item_id)
