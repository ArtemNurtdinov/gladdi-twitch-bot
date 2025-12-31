from typing import Optional

from app.twitch.application.common.model import StreamDataDTO
from app.twitch.application.common.stream_info_port import StreamInfoPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class StreamInfoAdapter(StreamInfoPort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_stream_info(self, channel_name: str) -> Optional[StreamDataDTO]:
        return await self._twitch_api_service.get_stream_info(channel_name)

