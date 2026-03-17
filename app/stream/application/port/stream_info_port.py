from typing import Protocol

from app.stream.application.models.stream_info import StreamInfoDTO
from app.stream.application.models.stream_status import StreamStatusDTO


class StreamInfoPort(Protocol):
    async def get_stream_info(self, channel_name: str) -> StreamInfoDTO | None: ...

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None: ...
