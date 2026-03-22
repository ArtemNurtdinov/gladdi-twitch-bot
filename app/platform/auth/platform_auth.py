from abc import ABC, abstractmethod


class PlatformAuth(ABC):
    client_id: str | None
    client_secret: str | None
    access_token: str
    refresh_token: str

    @abstractmethod
    async def update_access_token(self) -> None: ...

    @abstractmethod
    async def check_token_is_valid(self) -> bool: ...
