from abc import ABC, abstractmethod


class BalanceCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str): ...
