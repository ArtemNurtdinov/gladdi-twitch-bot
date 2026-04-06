from abc import ABC, abstractmethod

from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate, ShopItemPatch


class ShopItemRepository(ABC):
    @abstractmethod
    def get_all_items(self) -> list[ShopItem]: ...

    @abstractmethod
    async def get_item_by_id(self, shop_item_id: int) -> ShopItem | None: ...

    @abstractmethod
    def get_active_items(self) -> list[ShopItem]: ...

    @abstractmethod
    def get_active_item_by_name(self, name: str) -> ShopItem | None: ...

    @abstractmethod
    async def create_item(self, shop_item: ShopItemCreate) -> ShopItem: ...

    @abstractmethod
    def deactivate_item(self, item_id: int) -> None: ...

    @abstractmethod
    async def delete_item(self, item_id: int) -> None: ...

    @abstractmethod
    async def patch_shop_item(self, shop_item: ShopItemPatch) -> ShopItem | None: ...
