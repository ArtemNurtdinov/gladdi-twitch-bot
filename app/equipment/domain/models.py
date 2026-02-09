from dataclasses import dataclass
from datetime import datetime

from app.shop.domain.models import ShopItem, ShopItemType


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime
