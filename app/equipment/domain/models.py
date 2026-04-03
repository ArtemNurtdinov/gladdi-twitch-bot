from dataclasses import dataclass
from datetime import datetime

from app.shop.domain.model.shop_item import ShopItem


@dataclass
class UserEquipmentItem:
    shop_item: ShopItem
    expires_at: datetime
