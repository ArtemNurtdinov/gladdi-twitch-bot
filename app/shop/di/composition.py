from sqlalchemy.orm import Session

from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.di.dependencies import (
    provide_get_all_shop_items_use_case,
    provide_item_effect_mapper,
    provide_shop_item_mapper,
    provide_shop_item_mapper_dto,
    provide_shop_item_repository,
)


def get_all_shop_items_use_case(session: Session) -> GetAllShopItemsUseCase:
    shop_item_mapper = provide_shop_item_mapper()
    effect_mapper = provide_item_effect_mapper()
    shop_item_dto_mapper = provide_shop_item_mapper_dto(effect_mapper)
    shop_item_repository = provide_shop_item_repository(session, shop_item_mapper)
    all_shop_items_use_case = provide_get_all_shop_items_use_case(shop_item_repository, shop_item_dto_mapper)
    return all_shop_items_use_case
