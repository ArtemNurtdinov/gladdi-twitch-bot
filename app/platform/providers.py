from dataclasses import dataclass
from typing import Protocol

from app.platform.auth import PlatformAuth
from app.platform.streaming import StreamingPlatformPort


class PlatformApiClient(Protocol):
    async def aclose(self) -> None: ...


@dataclass
class PlatformProviders:
    platform_auth: PlatformAuth
    streaming_platform: StreamingPlatformPort
    api_client: PlatformApiClient | None = None
