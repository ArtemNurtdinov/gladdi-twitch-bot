from abc import ABC, abstractmethod
from datetime import datetime

from app.equipment.domain.model.user_equipment import UserEquipment


class EquipmentRepository(ABC):
    @abstractmethod
    def list_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipment]: ...

    @abstractmethod
    def add_equipment(self, channel_name: str, user_name: str, shop_item_id: int, expires_at: datetime) -> None: ...

    @abstractmethod
    def equipment_exists(self, channel_name: str, user_name: str, shop_item_id: int) -> bool: ...
