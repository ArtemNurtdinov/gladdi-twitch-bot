from dataclasses import dataclass

from app.shop.domain.model.effect import ItemEffect


@dataclass
class ShopItem:
    id: int
    channel_name: str
    name: str
    description: str
    price: int
    emoji: str
    effects: list[ItemEffect]


@dataclass
class ShopItemCreate:
    channel_name: str
    name: str
    description: str
    price: int
    emoji: str
    effects: list[ItemEffect]
