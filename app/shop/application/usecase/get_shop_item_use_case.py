from app.shop.application.mapper.shop_item_mapper import ShopItemMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.domain.repository import ShopItemRepository


class GetShopItemUseCase:
    def __init__(self, shop_item_repository: ShopItemRepository, mapper: ShopItemMapper):
        self._shop_item_repository = shop_item_repository
        self._mapper = mapper

    async def get_shop_item(self, shop_item_id: int) -> ShopItemDTO | None:
        shop_item = await self._shop_item_repository.get_item_by_id(shop_item_id)
        if shop_item is None:
            return None
        return self._mapper.to_dto(shop_item)
