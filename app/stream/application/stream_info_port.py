from typing import Protocol

from app.stream.application.model import StreamDataDTO


class StreamInfoPort(Protocol):
    async def get_stream_info(self, channel_name: str) -> StreamDataDTO | None: ...
