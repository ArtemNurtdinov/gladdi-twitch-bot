from abc import ABC, abstractmethod


class BackgroundJob(ABC):
    name: str

    @abstractmethod
    def apply_channel(self, channel_name: str, bot_name: str): ...

    @abstractmethod
    async def run(self): ...
