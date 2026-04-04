from dataclasses import dataclass
from datetime import datetime

from app.shop.domain.model.shop_item import ShopItem
from app.shop.domain.model.type import ShopItemType


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime
