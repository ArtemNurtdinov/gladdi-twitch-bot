from sqlalchemy.orm import Session

from app.shop.application.usecase.create_shop_item_use_case import CreateShopItemUseCase
from app.shop.application.usecase.delete_shop_item_use_case import DeleteShopItemUseCase
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.application.usecase.get_shop_item_use_case import GetShopItemUseCase
from app.shop.di.dependencies import (
    provide_create_shop_item_use_case,
    provide_delete_shop_item_use_case,
    provide_get_all_shop_items_use_case,
    provide_get_shop_item_use_case,
    provide_item_effect_mapper,
    provide_shop_item_effect_schema_mapper,
    provide_shop_item_mapper,
    provide_shop_item_mapper_dto,
    provide_shop_item_repository,
)
from app.shop.presentation.api.mapper.shop_item_effect_schema_mapper import ShopItemEffectSchemaMapper
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper


def get_all_shop_items_use_case(session: Session) -> GetAllShopItemsUseCase:
    shop_item_mapper = provide_shop_item_mapper()
    effect_mapper = provide_item_effect_mapper()
    shop_item_dto_mapper = provide_shop_item_mapper_dto(effect_mapper)
    shop_item_repository = provide_shop_item_repository(session, shop_item_mapper)
    all_shop_items_use_case = provide_get_all_shop_items_use_case(shop_item_repository, shop_item_dto_mapper)
    return all_shop_items_use_case


def get_shop_item_schema_mapper() -> ShopItemSchemaMapper:
    effect_mapper: ShopItemEffectSchemaMapper = provide_shop_item_effect_schema_mapper()
    return ShopItemSchemaMapper(effect_mapper=effect_mapper)


def get_create_shop_item_use_case(session: Session) -> CreateShopItemUseCase:
    shop_item_mapper = provide_shop_item_mapper()
    effect_mapper = provide_item_effect_mapper()
    shop_item_dto_mapper = provide_shop_item_mapper_dto(effect_mapper)
    shop_item_repository = provide_shop_item_repository(session, shop_item_mapper)
    create_shop_item_use_case = provide_create_shop_item_use_case(shop_item_repository, shop_item_dto_mapper)
    return create_shop_item_use_case


def get_delete_shop_item_use_case(session: Session) -> DeleteShopItemUseCase:
    shop_item_mapper = provide_shop_item_mapper()
    shop_item_repository = provide_shop_item_repository(session, shop_item_mapper)
    create_shop_item_use_case = provide_delete_shop_item_use_case(shop_item_repository)
    return create_shop_item_use_case


def get_shop_item_use_case(session: Session) -> GetShopItemUseCase:
    shop_item_mapper = provide_shop_item_mapper()
    effect_mapper = provide_item_effect_mapper()
    shop_item_dto_mapper = provide_shop_item_mapper_dto(effect_mapper)
    shop_item_repository = provide_shop_item_repository(session, shop_item_mapper)
    create_shop_item_use_case = provide_get_shop_item_use_case(shop_item_repository, shop_item_dto_mapper)
    return create_shop_item_use_case
