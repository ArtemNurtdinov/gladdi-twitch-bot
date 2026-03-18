from abc import ABC, abstractmethod


class HelpCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str): ...
