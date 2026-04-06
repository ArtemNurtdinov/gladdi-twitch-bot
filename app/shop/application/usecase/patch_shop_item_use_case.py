from app.shop.application.mapper.shop_item_mapper import ShopItemMapper
from app.shop.application.model.shop_item import ShopItemDTO
from app.shop.application.model.shop_item_patch import PatchShopItemDTO
from app.shop.domain.repository import ShopItemRepository


class PatchShopItemUseCase:
    def __init__(self, shop_item_repository: ShopItemRepository, mapper: ShopItemMapper):
        self._shop_item_repository = shop_item_repository
        self._mapper = mapper

    async def patch_shop_item(self, shop_item_patch: PatchShopItemDTO) -> ShopItemDTO | None:
        patch = self._mapper.map_patch_shop_item_to_domain(shop_item_patch)
        patch_result = await self._shop_item_repository.patch_shop_item(patch)
        if patch_result is None:
            return None
        return self._mapper.to_dto(patch_result)
