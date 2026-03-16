from abc import ABC, abstractmethod


class UserCachePort(ABC):
    @abstractmethod
    async def get_user_id(self, login: str) -> str | None: ...

    @abstractmethod
    async def warmup(self, login: str) -> None: ...
