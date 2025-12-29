from app.economy.domain.models import ShopItemType
from app.equipment.domain.repo import EquipmentRepository


class EquipmentExistsUseCase:

    def __init__(self, repo: EquipmentRepository):
        self._repo = repo

    def check_equipment_exists(self, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        return self._repo.equipment_exists(channel_name, user_name, item_type)
