from typing import Protocol


class PlatformAuth(Protocol):

    client_id: str | None
    client_secret: str | None
    access_token: str
    refresh_token: str

    async def update_access_token(self) -> None: ...

    async def check_token_is_valid(self) -> bool: ...
