from dataclasses import dataclass
from datetime import datetime

from app.shop.domain.model.shop_item import ShopItem


@dataclass
class UserEquipment:
    channel_name: str
    user_name: str
    shop_item_id: int
    shop_item: ShopItem
    expires_at: datetime
