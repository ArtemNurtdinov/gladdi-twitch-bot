from pydantic import BaseModel, Field

from app.shop.presentation.api.model.shop_item_schema import ShopItemSchema


class CreateShopItemResponse(BaseModel):
    shop_item: ShopItemSchema = Field(..., description="Созданный предмет в магазине")
