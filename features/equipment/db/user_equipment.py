from sqlalchemy import Column, String, DateTime, Integer, Enum
from datetime import datetime, timedelta

from db.base import Base
from features.economy.model.shop_items import ShopItemType


class UserEquipment(Base):
    __tablename__ = 'user_equipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    item_type = Column(Enum(ShopItemType), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserEquipment(user='{self.user_name}', item='{self.item_type}', expires={self.expires_at})>"
    
    def is_active(self) -> bool:
        return datetime.utcnow() < self.expires_at
    
    @staticmethod
    def get_expiry_date() -> datetime:
        return datetime.utcnow() + timedelta(days=30) 