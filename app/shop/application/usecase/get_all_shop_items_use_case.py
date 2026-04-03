from app.shop.application.mapper.shop_item_mapper import ShopItemMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.domain.repository import ShopItemRepository


class GetAllShopItemsUseCase:
    def __init__(self, shop_item_repository: ShopItemRepository, mapper: ShopItemMapper):
        self._shop_item_repository = shop_item_repository
        self._mapper = mapper

    async def get_all_items(self) -> list[ShopItemDTO]:
        items = self._shop_item_repository.get_all_items()
        return [self._mapper.to_dto(item) for item in items]
