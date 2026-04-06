from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.application.model.shop_item_create import CreateShopItemDTO
from app.shop.presentation.api.mapper.shop_item_effect_schema_mapper import ShopItemEffectSchemaMapper
from app.shop.presentation.api.model.request.create_shop_item_request import CreateShopItemRequest
from app.shop.presentation.api.model.shop_item_schema import ShopItemSchema


class ShopItemSchemaMapper:
    def __init__(self, effect_mapper: ShopItemEffectSchemaMapper):
        self._effect_mapper = effect_mapper

    def map_to_schema(self, shop_item: ShopItemDTO) -> ShopItemSchema:
        return ShopItemSchema(
            id=shop_item.id,
            channel_name=shop_item.channel_name,
            name=shop_item.name,
            description=shop_item.description,
            price=shop_item.price,
            emoji=shop_item.emoji,
            is_active=shop_item.is_active,
            effects=[self._effect_mapper.map_dto_to_schema(e) for e in shop_item.effects],
        )

    def map_create_to_dto(self, shop_item: CreateShopItemRequest) -> CreateShopItemDTO:
        return CreateShopItemDTO(
            channel_name=shop_item.channel_name,
            name=shop_item.name,
            description=shop_item.description,
            price=shop_item.price,
            emoji=shop_item.emoji,
            is_active=shop_item.is_active,
            effects=[self._effect_mapper.map_schema_to_dto(effect) for effect in shop_item.effects],
        )
