from pydantic import BaseModel, Field

from app.shop.presentation.api.model.shop_item_effect_schema import ItemEffectSchema


class PatchShopItemRequest(BaseModel):
    id: int = Field(..., description="ID предмета")
    channel_name: str | None = Field(None, description="Название канала", min_length=1, max_length=100)
    name: str | None = Field(None, description="Название предмета", min_length=1, max_length=255)
    description: str | None = Field(None, description="Описание предмета", min_length=1, max_length=1000)
    price: int | None = Field(None, description="Цена предмета", ge=0, le=1_000_000)
    emoji: str | None = Field(None, description="Эмодзи предмета", min_length=1, max_length=10)
    is_active: bool | None = Field(None, description="Доступен ли предмет для покупки")
    effects: list[ItemEffectSchema] | None = Field(None, description="Список эффектов")
