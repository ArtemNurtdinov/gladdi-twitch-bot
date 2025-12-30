from typing import List

from app.twitch.application.common.stream_chatters_port import StreamChattersPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class StreamChattersAdapter(StreamChattersPort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> List[str]:
        return await self._twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)

