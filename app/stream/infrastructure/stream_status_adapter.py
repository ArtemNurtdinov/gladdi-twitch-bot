from typing import Optional

from app.stream.application.model import StreamStatusDTO
from app.stream.application.stream_status_port import StreamStatusPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class StreamStatusAdapter(StreamStatusPort):

    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_stream_status(self, broadcaster_id: str) -> Optional[StreamStatusDTO]:
        return await self._twitch_api_service.get_stream_status(broadcaster_id)
