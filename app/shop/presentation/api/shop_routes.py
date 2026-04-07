from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.network.api.model.base_response import BaseResponse
from app.shop.application.usecase.create_shop_item_use_case import CreateShopItemUseCase
from app.shop.application.usecase.delete_shop_item_use_case import DeleteShopItemUseCase
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.application.usecase.get_shop_item_use_case import GetShopItemUseCase
from app.shop.application.usecase.patch_shop_item_use_case import PatchShopItemUseCase
from app.shop.di.composition import (
    get_all_shop_items_use_case,
    get_create_shop_item_use_case,
    get_delete_shop_item_use_case,
    get_patch_shop_item_use_case,
    get_shop_item_schema_mapper,
    get_shop_item_use_case,
)
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper
from app.shop.presentation.api.model.request.create_shop_item_request import CreateShopItemRequest
from app.shop.presentation.api.model.request.patch_shop_item_request import PatchShopItemRequest
from app.shop.presentation.api.model.response.all_shop_items_response import AllItemsResponse
from app.shop.presentation.api.model.response.create_shop_item_response import CreateShopItemResponse
from app.shop.presentation.api.model.shop_item_schema import ShopItemSchema
from core.db import db_ro_session, db_rw_session

router = APIRouter()


@router.get("/items", summary="Получение всех предметов магазина", response_model=AllItemsResponse)
async def get_all_shop_items(
    channel_name: str = Query(None),
    shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper),
) -> AllItemsResponse:
    if channel_name is None:
        raise HTTPException(status_code=400, detail="Необходим query параметр channel_name")

    with db_ro_session() as session:
        all_shop_items_use_case: GetAllShopItemsUseCase = get_all_shop_items_use_case(session)
        shop_items = await all_shop_items_use_case.get_all_items(channel_name)

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


@router.patch("/items/{shop_item_id}", summary="Отредактировать предмет", response_model=CreateShopItemResponse)
async def patch_item(
    body: PatchShopItemRequest, shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper)
) -> CreateShopItemResponse:
    shop_item_patch = shop_item_schema_mapper.map_patch_to_dto(body)

    with db_rw_session() as session:
        patch_shop_item_use_case: PatchShopItemUseCase = get_patch_shop_item_use_case(session)
        updated_item = await patch_shop_item_use_case.patch_shop_item(shop_item_patch)

    if updated_item is None:
        raise HTTPException(status_code=404, detail="Предмет в магазине не найден")

    shop_item = shop_item_schema_mapper.map_to_schema(updated_item)
    return CreateShopItemResponse(shop_item=shop_item)


@router.get("/items/{shop_item_id}", summary="Получить предмет по айди", response_model=ShopItemSchema)
async def get_shop_item(
    shop_item_id: int, shop_item_schema_mapper: ShopItemSchemaMapper = Depends(get_shop_item_schema_mapper)
) -> ShopItemSchema:
    with db_ro_session() as session:
        shop_item_use_case: GetShopItemUseCase = get_shop_item_use_case(session)
        shop_item = await shop_item_use_case.get_shop_item(shop_item_id)
    if shop_item is None:
        raise HTTPException(status_code=404, detail="Предмет в магазине не найден")
    return shop_item_schema_mapper.map_to_schema(shop_item)


@router.delete("/items/{shop_item_id}", summary="Удаление предмета из магазина", response_model=BaseResponse)
async def delete_item(
    shop_item_id: int,
) -> BaseResponse:
    with db_rw_session() as session:
        delete_shop_item_use_case: DeleteShopItemUseCase = get_delete_shop_item_use_case(session)
        await delete_shop_item_use_case.execute(shop_item_id)
    return BaseResponse(message="Предмет успешно удалён")
