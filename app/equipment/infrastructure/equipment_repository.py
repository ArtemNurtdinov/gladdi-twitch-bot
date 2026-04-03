from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.equipment.domain.model.user_equipment import UserEquipment
from app.equipment.domain.repo import EquipmentRepository
from app.equipment.infrastructure.db.user_equipment import UserEquipment as OrmUserEquipment
from app.equipment.infrastructure.mapper.user_equipment_mapper import UserEquipmentMapper


class EquipmentRepositoryImpl(EquipmentRepository):
    def __init__(self, db: Session, mapper: UserEquipmentMapper):
        self._db = db
        self._mapper = mapper

    def list_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipment]:
        stmt = (
            select(OrmUserEquipment)
            .where(OrmUserEquipment.channel_name == channel_name)
            .where(OrmUserEquipment.user_name == user_name)
            .where(OrmUserEquipment.expires_at > datetime.utcnow())
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(item) for item in rows]

    def add_equipment(self, channel_name: str, user_name: str, shop_item_id: int, expires_at: datetime) -> None:
        orm = OrmUserEquipment(
            channel_name=channel_name,
            user_name=user_name,
            shop_item_id=shop_item_id,
            expires_at=expires_at,
        )
        self._db.add(orm)

    def equipment_exists(self, channel_name: str, user_name: str, shop_item_id: int) -> bool:
        stmt = (
            select(OrmUserEquipment)
            .where(OrmUserEquipment.channel_name == channel_name)
            .where(OrmUserEquipment.user_name == user_name)
            .where(OrmUserEquipment.shop_item_id == shop_item_id)
            .where(OrmUserEquipment.expires_at > datetime.utcnow())
        )
        existing_item = self._db.execute(stmt).scalars().first()
        return existing_item is not None
