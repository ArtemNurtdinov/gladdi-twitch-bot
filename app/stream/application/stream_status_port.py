from typing import Protocol

from app.stream.application.model import StreamStatusDTO


class StreamStatusPort(Protocol):
    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None: ...
