from typing import Protocol, Generic, TypeVar

from app.equipment.domain.models import UserEquipmentItem
from app.economy.domain.models import ShopItemType

DB = TypeVar("DB")


class EquipmentRepository(Protocol, Generic[DB]):

    def list_user_equipment(self, db: DB, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        ...

    def add_equipment(self, db: DB, channel_name: str, user_name: str, item: UserEquipmentItem) -> None:
        ...

    def equipment_exists(self, db: DB, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        ...

