from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.economy.domain.models import ShopItemType
from core.db import Base


class UserEquipment(Base):
    __tablename__ = "user_equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    item_type = Column(Enum(ShopItemType), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
