from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shop.infrastructure.db.model.shop_item import ShopItem
from core.db import Base


class UserEquipment(Base):
    __tablename__ = "user_equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    shop_item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    item: Mapped[ShopItem] = relationship(ShopItem, foreign_keys=[shop_item_id], lazy="joined")
