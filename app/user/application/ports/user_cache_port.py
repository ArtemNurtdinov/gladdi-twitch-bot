from typing import Protocol


class UserCachePort(Protocol):
    async def get_user_id(self, login: str) -> str | None: ...

    async def warmup(self, login: str) -> None: ...
