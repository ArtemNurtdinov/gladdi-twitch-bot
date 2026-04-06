from pydantic import BaseModel, Field

from app.shop.presentation.api.model.shop_item_schema import ShopItemSchema


class AllItemsResponse(BaseModel):
    shop_items: list[ShopItemSchema] = Field(..., description="Все предметы магазина")
