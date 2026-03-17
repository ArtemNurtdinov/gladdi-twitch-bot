from __future__ import annotations

from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.model import FollowageInfo
from app.follow.application.models.follower import ChannelFollowerDTO
from app.moderation.application.moderation_port import ModerationPort
from app.platform.infrastructure.api_client import StreamingApiClient
from app.stream.application.models.stream_info import StreamInfoDTO
from app.stream.application.models.stream_status import StreamStatusDTO
from app.stream.application.port.stream_info_port import StreamInfoPort
from app.user.application.model.model import UserInfoDTO
from app.user.application.ports.user_info_port import UserInfoPort
from app.viewer.application.ports.stream_chatters_port import StreamChattersPort


class TwitchApiService(
    FollowagePort,
    StreamInfoPort,
    UserInfoPort,
    StreamChattersPort,
    ModerationPort,
):
    def __init__(
        self,
        streaming_client: StreamingApiClient,
        user_info_port: UserInfoPort,
        followage_port: FollowagePort,
        stream_info_port: StreamInfoPort,
        stream_chatters_port: StreamChattersPort,
        moderation_port: ModerationPort,
    ):
        self._streaming_client = streaming_client
        self._user_info_port = user_info_port
        self._followage_port = followage_port
        self._stream_info_port = stream_info_port
        self._stream_chatters_port = stream_chatters_port
        self._moderation_port = moderation_port

    async def aclose(self) -> None:
        await self._streaming_client.aclose()

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        return await self._user_info_port.get_user_by_login(login)

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        return await self._followage_port.get_followage(channel_name, user_id)

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        return await self._followage_port.get_channel_followers(channel_name)

    async def get_stream_status(self, broadcaster_id: str) -> StreamStatusDTO | None:
        return await self._stream_info_port.get_stream_status(broadcaster_id)

    async def get_stream_info(self, channel_name: str) -> StreamInfoDTO | None:
        return await self._stream_info_port.get_stream_info(channel_name)

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]:
        return await self._stream_chatters_port.get_stream_chatters(broadcaster_id, moderator_id)

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        return await self._moderation_port.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
