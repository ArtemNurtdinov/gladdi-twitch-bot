from datetime import datetime, timedelta

from app.economy.domain.models import ShopItems, ShopItemType
from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory
from app.equipment.domain.models import UserEquipmentItem


class AddEquipmentUseCase:
    def __init__(self, unit_of_work_factory: EquipmentUseCaseUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def add(self, channel_name: str, user_name: str, item_type: ShopItemType):
        expires_at = datetime.utcnow() + timedelta(days=30)
        item = UserEquipmentItem(item_type=item_type, shop_item=ShopItems.get_item(item_type), expires_at=expires_at)
        with self._unit_of_work_factory.create() as uow:
            uow.equipment_repo.add_equipment(channel_name, user_name, item)
