from sqlalchemy import Column, String, DateTime, Integer, Enum
from datetime import datetime

from core.db import Base
from features.economy.domain.models import ShopItemType


class UserEquipment(Base):
    __tablename__ = 'user_equipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    item_type = Column(Enum(ShopItemType), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
