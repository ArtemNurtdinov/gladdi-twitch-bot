from typing import Protocol


class OAuthSession(Protocol):
    access_token: str
    refresh_token: str

    async def validate(self) -> bool: ...
    async def refresh(self) -> None: ...
