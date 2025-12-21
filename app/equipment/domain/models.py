from dataclasses import dataclass
from app.economy.domain.models import ShopItemType, ShopItem
from datetime import datetime


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime