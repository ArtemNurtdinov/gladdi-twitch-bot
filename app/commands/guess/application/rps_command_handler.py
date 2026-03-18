from abc import ABC, abstractmethod


class RpsCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str, choice: str | None): ...
