from abc import ABC, abstractmethod


class ViewerCachePort(ABC):
    @abstractmethod
    async def get_viewer_id(self, login: str) -> str | None: ...

    @abstractmethod
    async def warmup(self, login: str) -> None: ...
