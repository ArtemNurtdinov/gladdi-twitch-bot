from app.platform.streaming import StreamingPlatformPort
from app.viewer.application.stream_chatters_port import StreamChattersPort


class StreamChattersAdapter(StreamChattersPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]:
        return await self._platform.get_stream_chatters(broadcaster_id, moderator_id)
