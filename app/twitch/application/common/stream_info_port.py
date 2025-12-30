from typing import Optional, Protocol

from app.twitch.application.common.model import StreamDataDTO


class StreamInfoPort(Protocol):

    async def get_stream_info(self, channel_login: str) -> Optional[StreamDataDTO]:
        ...
