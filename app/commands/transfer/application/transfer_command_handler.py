from abc import ABC, abstractmethod


class TransferCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, sender_display_name: str, recipient: str | None = None, amount: str | None = None): ...
