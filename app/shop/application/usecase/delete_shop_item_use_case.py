from app.shop.domain.repository import ShopItemRepository


class DeleteShopItemUseCase:
    def __init__(self, shop_item_repository: ShopItemRepository):
        self._shop_item_repository = shop_item_repository

    async def execute(self, item_id: int) -> None:
        await self._shop_item_repository.delete_item(item_id)
