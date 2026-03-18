from abc import ABC, abstractmethod


class RollCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str, amount: str | None = None): ...
