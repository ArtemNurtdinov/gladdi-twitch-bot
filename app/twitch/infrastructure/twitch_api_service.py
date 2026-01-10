from __future__ import annotations

from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.model import FollowageInfo
from app.follow.application.model import ChannelFollowerDTO
from app.moderation.application.moderation_port import ModerationPort
from app.stream.application.model import StreamDataDTO, StreamStatusDTO
from app.stream.application.stream_info_port import StreamInfoPort
from app.stream.application.stream_status_port import StreamStatusPort
from app.user.application.model import UserInfoDTO
from app.user.application.user_info_port import UserInfoPort
from app.viewer.application.stream_chatters_port import StreamChattersPort
from core.platform.api_client import StreamingApiClient


class TwitchApiService(
    FollowagePort,
    StreamInfoPort,
    StreamStatusPort,
    UserInfoPort,
    StreamChattersPort,
    ModerationPort,
):
    def __init__(
        self,
        *,
        client: StreamingApiClient,
        user_info_adapter: UserInfoPort,
        followage_adapter: FollowagePort,
        stream_info_adapter: StreamInfoPort,
        stream_status_adapter: StreamStatusPort,
        chatters_adapter: StreamChattersPort,
        moderation_adapter: ModerationPort,
    ):
        self._client = client
        self._user_info_adapter = user_info_adapter
        self._followage_adapter = followage_adapter
        self._stream_info_adapter = stream_info_adapter
        self._stream_status_adapter = stream_status_adapter
        self._chatters_adapter = chatters_adapter
        self._moderation_adapter = moderation_adapter

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        return await self._user_info_adapter.get_user_by_login(login)

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        return await self._followage_adapter.get_followage(channel_name, user_id)

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        return await self._followage_adapter.get_channel_followers(channel_name)

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None:
        return await self._stream_status_adapter.get_stream_status(broadcaster_id)

    async def get_stream_info(self, channel_name: str) -> StreamDataDTO | None:
        return await self._stream_info_adapter.get_stream_info(channel_name)

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]:
        return await self._chatters_adapter.get_stream_chatters(broadcaster_id, moderator_id)

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        return await self._moderation_adapter.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
