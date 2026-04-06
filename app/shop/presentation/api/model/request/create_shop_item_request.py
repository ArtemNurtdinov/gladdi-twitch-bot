from pydantic import BaseModel, Field

from app.shop.presentation.api.model.shop_item_effect_schema import ItemEffectSchema


class CreateShopItemRequest(BaseModel):
    channel_name: str = Field(..., description="Название канала", min_length=1, max_length=100)
    name: str = Field(..., description="Название предмета", min_length=1, max_length=255)
    description: str = Field(..., description="Описание предмета", min_length=1, max_length=1000)
    price: int = Field(..., description="Цена предмета в монетах", ge=0, le=1_000_000)
    emoji: str = Field(..., description="Эмодзи предмета", min_length=1, max_length=10)
    is_active: bool = Field(default=True, description="Доступен ли предмет для покупки")
    effects: list[ItemEffectSchema] = Field(default_factory=list, description="Список эффектов")
