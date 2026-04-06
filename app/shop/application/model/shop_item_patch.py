from dataclasses import dataclass

from app.shop.application.model.effect import ItemEffectDTO


@dataclass(frozen=True)
class PatchShopItemDTO:
    id: int
    channel_name: str | None
    name: str | None
    description: str | None
    price: int | None
    emoji: str | None
    is_active: bool | None
    effects: list[ItemEffectDTO] | None
