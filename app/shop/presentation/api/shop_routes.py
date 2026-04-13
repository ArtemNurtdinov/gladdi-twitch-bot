from fastapi import APIRouter, HTTPException, Query

from app.core.network.api.model.base_response import BaseResponse
from app.shop.di.container import ShopContainer
from app.shop.presentation.api.model.request.create_shop_item_request import CreateShopItemRequest
from app.shop.presentation.api.model.request.patch_shop_item_request import PatchShopItemRequest
from app.shop.presentation.api.model.response.all_shop_items_response import AllItemsResponse
from app.shop.presentation.api.model.response.create_shop_item_response import CreateShopItemResponse
from app.shop.presentation.api.model.shop_item_schema import ShopItemSchema
from core.db import db_ro_session, db_rw_session

router = APIRouter()


@router.get("/items", summary="Получение всех предметов магазина", response_model=AllItemsResponse)
async def get_all_shop_items(
    channel_name: str = Query(..., description="Имя канала"),
) -> AllItemsResponse:
    container = ShopContainer()
    with db_ro_session() as session:
        shop_items = await container.get_all_use_case(session).get_all_items(channel_name)
    items = [container.shop_item_schema_mapper.map_to_schema(item) for item in shop_items]
    return AllItemsResponse(shop_items=items)


@router.post("/items", summary="Создание предмета в магазине", response_model=CreateShopItemResponse)
async def create_item(
    body: CreateShopItemRequest,
) -> CreateShopItemResponse:
    container = ShopContainer()
    shop_item_create = container.shop_item_schema_mapper.map_create_to_dto(body)
    with db_rw_session() as session:
        created_item = await container.create_shop_item_use_case(session).create(shop_item_create)
    shop_item = container.shop_item_schema_mapper.map_to_schema(created_item)
    return CreateShopItemResponse(shop_item=shop_item)


@router.patch("/items/{shop_item_id}", summary="Отредактировать предмет", response_model=CreateShopItemResponse)
async def patch_item(
    body: PatchShopItemRequest,
) -> CreateShopItemResponse:
    container = ShopContainer()
    shop_item_patch = container.shop_item_schema_mapper.map_patch_to_dto(body)
    with db_rw_session() as session:
        updated_item = await container.patch_shop_item_use_case(session).patch_shop_item(shop_item_patch)

    if updated_item is None:
        raise HTTPException(status_code=404, detail="Предмет в магазине не найден")

    shop_item = container.shop_item_schema_mapper.map_to_schema(updated_item)
    return CreateShopItemResponse(shop_item=shop_item)


@router.get("/items/{shop_item_id}", summary="Получить предмет по айди", response_model=ShopItemSchema)
async def get_shop_item(
    shop_item_id: int,
) -> ShopItemSchema:
    container = ShopContainer()
    with db_ro_session() as session:
        shop_item = await container.get_shop_item_use_case(session).get_shop_item(shop_item_id)
    if shop_item is None:
        raise HTTPException(status_code=404, detail="Предмет в магазине не найден")
    return container.shop_item_schema_mapper.map_to_schema(shop_item)


@router.delete("/items/{shop_item_id}", summary="Удаление предмета из магазина", response_model=BaseResponse)
async def delete_item(
    shop_item_id: int,
) -> BaseResponse:
    container = ShopContainer()
    with db_rw_session() as session:
        await container.delete_shop_item_use_case(session).execute(shop_item_id)
    return BaseResponse(message="Предмет успешно удалён")
