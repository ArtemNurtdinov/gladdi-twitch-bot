from typing import Protocol

from app.stream.application.models.stream_info import StreamInfoDTO


class StreamInfoPort(Protocol):
    async def get_stream_info(self, channel_name: str) -> StreamInfoDTO | None: ...
