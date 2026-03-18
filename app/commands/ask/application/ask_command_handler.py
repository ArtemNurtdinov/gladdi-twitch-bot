from abc import ABC, abstractmethod


class AskCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, full_message: str, display_name: str): ...
