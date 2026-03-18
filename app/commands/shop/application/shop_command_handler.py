from abc import ABC, abstractmethod


class ShopCommandHandler(ABC):
    @abstractmethod
    async def handle_shop(self, channel_name: str, display_name: str): ...

    @abstractmethod
    async def handle_buy(self, channel_name: str, display_name: str, item_name: str | None): ...
