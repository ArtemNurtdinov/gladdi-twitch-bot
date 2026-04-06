from dataclasses import dataclass

from app.shop.domain.model.effect import ItemEffect


@dataclass(frozen=True)
class ShopItem:
    id: int
    channel_name: str
    name: str
    description: str
    price: int
    emoji: str
    is_active: bool
    effects: list[ItemEffect]


@dataclass(frozen=True)
class ShopItemCreate:
    channel_name: str
    name: str
    description: str
    price: int
    emoji: str
    is_active: bool
    effects: list[ItemEffect]


@dataclass(frozen=True)
class ShopItemPatch:
    id: int
    channel_name: str | None
    name: str | None
    description: str | None
    price: int | None
    emoji: str | None
    is_active: bool | None
    effects: list[ItemEffect] | None
