from __future__ import annotations

from app.platform.streaming import StreamingPlatformPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class TwitchStreamingPlatformAdapter(StreamingPlatformPort):
    def __init__(self, api: TwitchApiService):
        self._api = api

    async def get_user_by_login(self, login: str):
        return await self._api.get_user_by_login(login)

    async def get_followage(self, channel_name: str, user_id: str):
        return await self._api.get_followage(channel_name, user_id)

    async def get_channel_followers(self, channel_name: str):
        return await self._api.get_channel_followers(channel_name)

    async def get_stream_status(self, broadcaster_id: str):
        return await self._api.get_stream_status(broadcaster_id)

    async def get_stream_info(self, channel_name: str):
        return await self._api.get_stream_info(channel_name)

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str):
        return await self._api.get_stream_chatters(broadcaster_id, moderator_id)

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str):
        return await self._api.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
