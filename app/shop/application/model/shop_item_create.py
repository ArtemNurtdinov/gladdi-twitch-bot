from dataclasses import dataclass

from app.shop.application.model.effect import ItemEffectDTO


@dataclass(frozen=True)
class CreateShopItemDTO:
    channel_name: str
    name: str
    description: str
    price: int
    emoji: str
    is_active: bool
    effects: list[ItemEffectDTO]
