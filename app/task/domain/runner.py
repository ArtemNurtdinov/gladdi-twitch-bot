from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable


class TaskRunner(ABC):
    @abstractmethod
    def register(self, name: str, coro_factory: Callable[[], Awaitable[None]]): ...

    @abstractmethod
    def start_all(self): ...

    @abstractmethod
    async def cancel_all(self): ...
