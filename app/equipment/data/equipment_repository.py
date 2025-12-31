from datetime import datetime

from sqlalchemy.orm import Session

from app.economy.domain.models import ShopItems, ShopItemType
from app.equipment.data.db.user_equipment import UserEquipment as OrmUserEquipment
from app.equipment.domain.models import UserEquipmentItem
from app.equipment.domain.repo import EquipmentRepository


def _to_domain_item(row: OrmUserEquipment) -> UserEquipmentItem:
    shop_item = ShopItems.get_item(row.item_type)
    return UserEquipmentItem(item_type=row.item_type, shop_item=shop_item, expires_at=row.expires_at)


class EquipmentRepositoryImpl(EquipmentRepository):
    def __init__(self, db: Session):
        self._db = db

    def list_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        rows = (
            self._db.query(OrmUserEquipment)
            .filter_by(channel_name=channel_name, user_name=user_name)
            .filter(OrmUserEquipment.expires_at > datetime.utcnow())
            .all()
        )
        return [_to_domain_item(r) for r in rows]

    def add_equipment(self, channel_name: str, user_name: str, item: UserEquipmentItem) -> None:
        orm = OrmUserEquipment(
            channel_name=channel_name,
            user_name=user_name,
            item_type=item.item_type,
            expires_at=item.expires_at,
        )
        self._db.add(orm)

    def equipment_exists(self, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        existing_item = (
            self._db.query(OrmUserEquipment)
            .filter_by(channel_name=channel_name, user_name=user_name, item_type=item_type)
            .filter(OrmUserEquipment.expires_at > datetime.utcnow())
            .first()
        )
        return existing_item is not None
