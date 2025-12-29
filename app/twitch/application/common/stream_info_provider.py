from typing import Optional, Protocol

from app.twitch.application.common.model import StreamInfoDTO


class StreamInfoProvider(Protocol):

    async def get_stream_info(self, channel_login: str) -> Optional[StreamInfoDTO]:
        ...
