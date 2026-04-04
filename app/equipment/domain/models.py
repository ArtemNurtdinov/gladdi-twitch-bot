from dataclasses import dataclass
from datetime import datetime

from app.shop.domain.model.type import ShopItemType
from app.shop.domain.models import ShopItem


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime
