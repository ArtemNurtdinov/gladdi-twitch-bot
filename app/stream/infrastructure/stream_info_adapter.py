from app.platform.streaming import StreamingPlatformPort
from app.stream.application.model import StreamDataDTO
from app.stream.application.stream_info_port import StreamInfoPort


class StreamInfoAdapter(StreamInfoPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_stream_info(self, channel_name: str) -> StreamDataDTO | None:
        return await self._platform.get_stream_info(channel_name)
