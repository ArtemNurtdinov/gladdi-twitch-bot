from datetime import datetime, timedelta

from app.economy.domain.models import ShopItemType, ShopItems
from app.equipment.domain.models import UserEquipmentItem
from app.equipment.domain.repo import EquipmentRepository


class AddEquipmentUseCase:

    def __init__(self, repo: EquipmentRepository):
        self._repo = repo

    def add(self, channel_name: str, user_name: str, item_type: ShopItemType):
        expires_at = datetime.utcnow() + timedelta(days=30)
        item = UserEquipmentItem(item_type=item_type, shop_item=ShopItems.get_item(item_type), expires_at=expires_at)
        self._repo.add_equipment(channel_name, user_name, item)
