from fastapi import APIRouter, Depends

from app.core.network.api.model.base_response import BaseResponse
from app.shop.application.usecase.create_shop_item_use_case import CreateShopItemUseCase
from app.shop.application.usecase.delete_shop_item_use_case import DeleteShopItemUseCase
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.di.composition import (
    get_all_shop_items_use_case,
    get_create_shop_item_use_case,
    get_delete_shop_item_use_case,
    get_shop_item_schema_mapper,
)
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper
from app.shop.presentation.api.model.request.create_shop_item_request import CreateShopItemRequest
from app.shop.presentation.api.model.response.all_shop_items_response import AllItemsResponse
from app.shop.presentation.api.model.response.create_shop_item_response import CreateShopItemResponse
from core.db import db_ro_session, db_rw_session

router = APIRouter()


@router.get("/items", summary="Получение всех предметов магазина", response_model=AllItemsResponse)
async def get_all_shop_items(shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper)) -> AllItemsResponse:
    with db_ro_session() as session:
        all_shop_items_use_case: GetAllShopItemsUseCase = get_all_shop_items_use_case(session)
        shop_items = await all_shop_items_use_case.get_all_items()

    items = [shop_item_schema_mapper.map_to_schema(item) for item in shop_items]
    return AllItemsResponse(shop_items=items)


@router.post("/items", summary="Создание предмета в магазине", response_model=CreateShopItemResponse)
async def create_item(
    body: CreateShopItemRequest, shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper)
) -> CreateShopItemResponse:
    shop_item_create = shop_item_schema_mapper.map_create_to_dto(body)

    with db_rw_session() as session:
        create_shop_item_use_case: CreateShopItemUseCase = get_create_shop_item_use_case(session)
        created_item = await create_shop_item_use_case.create(shop_item_create)

    shop_item = shop_item_schema_mapper.map_to_schema(created_item)
    return CreateShopItemResponse(shop_item=shop_item)


@router.delete("/items/{shop_item_id}", summary="Удаление предмета из магазина", response_model=BaseResponse)
async def delete_item(
    shop_item_id: int,
) -> BaseResponse:
    with db_rw_session() as session:
        delete_shop_item_use_case: DeleteShopItemUseCase = get_delete_shop_item_use_case(session)
        await delete_shop_item_use_case.execute(shop_item_id)
    return BaseResponse(message="Предмет успешно удалён")
