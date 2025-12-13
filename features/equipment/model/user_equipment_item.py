from dataclasses import dataclass
from features.economy.model.shop_items import ShopItemType, ShopItem
from datetime import datetime


@dataclass
class UserEquipmentItem:
    item_type: ShopItemType
    shop_item: ShopItem
    expires_at: datetime
