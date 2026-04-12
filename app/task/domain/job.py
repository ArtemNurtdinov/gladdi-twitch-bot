from abc import ABC, abstractmethod


class BackgroundJob(ABC):
    name: str

    @abstractmethod
    async def run(self): ...
