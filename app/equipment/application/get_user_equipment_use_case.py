from app.equipment.domain.models import UserEquipmentItem
from app.equipment.domain.repo import EquipmentRepository


class GetUserEquipmentUseCase:
    def __init__(self, repo: EquipmentRepository):
        self._repo = repo

    def get_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        return self._repo.list_user_equipment(channel_name, user_name)
