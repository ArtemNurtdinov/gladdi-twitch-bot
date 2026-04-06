from fastapi import APIRouter

from app.shop.di.composition import get_all_shop_items_use_case
from app.shop.presentation.api.model.all_shop_items_response import AllItemsResponse
from core.db import db_ro_session

router = APIRouter()


@router.get("/items", summary="Получение всех предметов магазина", response_model=AllItemsResponse)
async def get_all_shop_items() -> AllItemsResponse:
    with db_ro_session() as session:
        all_shop_items_use_case = get_all_shop_items_use_case(session)
        shop_items = all_shop_items_use_case.get_all_items()
