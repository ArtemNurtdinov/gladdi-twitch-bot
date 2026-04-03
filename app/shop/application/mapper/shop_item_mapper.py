from app.shop.application.mapper.effect_mapper import EffectMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.domain.model.shop_item import ShopItem


class ShopItemMapper:
    def __init__(self, effect_mapper: EffectMapper):
        self._effect_mapper = effect_mapper

    def to_dto(self, shop_item: ShopItem) -> ShopItemDTO:
        return ShopItemDTO(
            id=shop_item.id,
            channel_name=shop_item.channel_name,
            name=shop_item.name,
            description=shop_item.description,
            price=shop_item.price,
            emoji=shop_item.emoji,
            effects=[self._effect_mapper.map_effect_to_dto(effect) for effect in shop_item.effects],
            is_active=shop_item.is_active,
        )

    def to_domain(self, dto: ShopItemDTO) -> ShopItem:
        return ShopItem(
            id=dto.id,
            channel_name=dto.channel_name,
            name=dto.name,
            description=dto.description,
            price=dto.price,
            emoji=dto.emoji,
            effects=[self._effect_mapper.map_effect_to_domain(effect) for effect in dto.effects],
            is_active=dto.is_active,
        )
