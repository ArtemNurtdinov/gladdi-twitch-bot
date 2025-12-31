from typing import Protocol

from app.economy.domain.models import ShopItemType
from app.equipment.domain.models import UserEquipmentItem


class EquipmentRepository(Protocol):
    def list_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]: ...

    def add_equipment(self, channel_name: str, user_name: str, item: UserEquipmentItem) -> None: ...

    def equipment_exists(self, channel_name: str, user_name: str, item_type: ShopItemType) -> bool: ...
