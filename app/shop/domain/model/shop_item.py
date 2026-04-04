from dataclasses import dataclass

from app.shop.domain.model.effect import ItemEffect


@dataclass
class ShopItem:
    name: str
    description: str
    price: int
    emoji: str
    effects: list[ItemEffect]
