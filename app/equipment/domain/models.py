from dataclasses import dataclass
from datetime import datetime

from app.economy.domain.models import ShopItem, ShopItemType


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime
