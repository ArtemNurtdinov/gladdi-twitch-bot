from abc import ABC, abstractmethod

from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate


class ShopItemRepository(ABC):
    @abstractmethod
    def get_active_items(self) -> list[ShopItem]: ...

    @abstractmethod
    def get_active_item_by_name(self, name: str) -> ShopItem | None: ...

    @abstractmethod
    def create_item(self, shop_item: ShopItemCreate, is_active: bool): ...

    @abstractmethod
    def deactivate_item(self, item_id: int) -> None: ...
