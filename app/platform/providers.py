from typing import Protocol


class PlatformApiClient(Protocol):
    async def aclose(self) -> None: ...
