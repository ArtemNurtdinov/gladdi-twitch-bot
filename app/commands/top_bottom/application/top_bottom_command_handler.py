from abc import ABC, abstractmethod


class TopBottomCommandHandler(ABC):
    @abstractmethod
    async def handle_top(self, channel_name: str, display_name: str): ...

    @abstractmethod
    async def handle_bottom(self, channel_name: str, display_name: str): ...
