from app.shop.application.mapper.effect_mapper import EffectMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.application.model.shop_item_create import CreateShopItemDTO
from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate


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

    def map_create_shop_item_to_domain(self, shop_item_create: CreateShopItemDTO) -> ShopItemCreate:
        effects = [self._effect_mapper.map_effect_to_domain(effect) for effect in shop_item_create.effects]
        return ShopItemCreate(
            channel_name=shop_item_create.channel_name,
            name=shop_item_create.name,
            description=shop_item_create.description,
            price=shop_item_create.price,
            emoji=shop_item_create.emoji,
            is_active=shop_item_create.is_active,
            effects=effects,
        )
