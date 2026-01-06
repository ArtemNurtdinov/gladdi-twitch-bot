from app.platform.streaming import StreamingPlatformPort
from app.stream.application.model import StreamStatusDTO
from app.stream.application.stream_status_port import StreamStatusPort


class StreamStatusAdapter(StreamStatusPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None:
        return await self._platform.get_stream_status(broadcaster_id)
