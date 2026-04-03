from sqlalchemy.orm import Session

from app.shop.application.mapper.effect_mapper import EffectMapper
from app.shop.application.mapper.shop_item_mapper import ShopItemMapper as ShopItemDTOMapper
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.domain.repository import ShopItemRepository
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from app.shop.infrastructure.repository import ShopItemRepositoryImpl
from app.shop.presentation.api.mapper.shop_item_effect_schema_mapper import ShopItemEffectSchemaMapper
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper


def provide_shop_item_mapper() -> ShopItemMapper:
    return ShopItemMapper()


def provide_item_effect_mapper() -> EffectMapper:
    return EffectMapper()


def provide_shop_item_mapper_dto(effect_mapper: EffectMapper) -> ShopItemDTOMapper:
    return ShopItemDTOMapper(effect_mapper=effect_mapper)


def provide_shop_item_repository(db: Session, mapper: ShopItemMapper) -> ShopItemRepository:
    return ShopItemRepositoryImpl(db=db, mapper=mapper)


def provide_get_all_shop_items_use_case(
    shop_item_repository: ShopItemRepository,
    shop_item_mapper: ShopItemDTOMapper,
) -> GetAllShopItemsUseCase:
    return GetAllShopItemsUseCase(shop_item_repository, shop_item_mapper)


def provide_shop_item_effect_schema_mapper() -> ShopItemEffectSchemaMapper:
    return ShopItemEffectSchemaMapper()


def provide_shop_item_schema_mapper(effect_schema_mapper: ShopItemEffectSchemaMapper) -> ShopItemSchemaMapper:
    return ShopItemSchemaMapper(effect_schema_mapper)
