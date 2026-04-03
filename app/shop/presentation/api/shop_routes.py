from fastapi import APIRouter, Depends

from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.di.composition import get_all_shop_items_use_case, get_shop_item_schema_mapper
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper
from app.shop.presentation.api.model.all_shop_items_response import AllItemsResponse
from core.db import db_ro_session

router = APIRouter()


@router.get("/items", summary="Получение всех предметов магазина", response_model=AllItemsResponse)
async def get_all_shop_items(shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper)) -> AllItemsResponse:
    with db_ro_session() as session:
        all_shop_items_use_case: GetAllShopItemsUseCase = get_all_shop_items_use_case(session)
        shop_items = await all_shop_items_use_case.get_all_items()
        items = [shop_item_schema_mapper.map_to_schema(item) for item in shop_items]
        return AllItemsResponse(shop_items=items)
