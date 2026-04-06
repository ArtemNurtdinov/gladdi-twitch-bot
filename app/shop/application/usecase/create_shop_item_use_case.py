from app.shop.application.mapper.shop_item_mapper import ShopItemMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.application.model.shop_item_create import CreateShopItemDTO
from app.shop.domain.repository import ShopItemRepository


class CreateShopItemUseCase:
    def __init__(self, shop_item_repository: ShopItemRepository, mapper: ShopItemMapper):
        self._shop_item_repository = shop_item_repository
        self._mapper = mapper

    async def create(self, shop_item_create: CreateShopItemDTO) -> ShopItemDTO:
        shop_item_create_domain = self._mapper.map_create_shop_item_to_domain(shop_item_create)
        created_item = await self._shop_item_repository.create_item(shop_item_create_domain)
        return self._mapper.to_dto(created_item)
