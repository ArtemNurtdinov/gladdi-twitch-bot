from __future__ import annotations

from pydantic import ValidationError

from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.model import FollowageInfo
from app.follow.application.model import ChannelFollowerDTO
from app.twitch.infrastructure.adapters.user_info_adapter import UserInfoApiAdapter
from core.platform.api_client import StreamingApiClient
from app.twitch.infrastructure.api_common import handle_api_response
from app.twitch.infrastructure.twitch_api_models import FollowerData, FollowersResponse


class FollowageApiAdapter(FollowagePort):
    def __init__(self, client: StreamingApiClient, user_info: UserInfoApiAdapter):
        self._client = client
        self._user_info = user_info

    async def _get_user_followage(self, broadcaster_id: str, user_id: str) -> FollowageInfo | None:
        response = await self._client.get("/channels/followers", params={"broadcaster_id": broadcaster_id, "user_id": user_id})
        try:
            data = await handle_api_response(response, f"get_user_followage({broadcaster_id}, {user_id})")
            parsed: FollowersResponse = FollowersResponse.model_validate(data)
        except ValidationError:
            return None

        followers: list[FollowerData] = parsed.data
        if followers:
            follow_data = followers[0]
            follow_dt = follow_data.followed_at.replace(tzinfo=None)
            return FollowageInfo(
                user_id=follow_data.user_id,
                user_name=follow_data.user_name,
                user_login=follow_data.user_login,
                followed_at=follow_dt,
            )
        return None

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        user = await self._user_info.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return None
        return await self._get_user_followage(broadcaster_id=broadcaster_id, user_id=user_id)

    async def _get_channel_followers(self, broadcaster_id: str) -> list[ChannelFollowerDTO]:
        params = {"broadcaster_id": broadcaster_id, "first": 100}
        followers: list[ChannelFollowerDTO] = []
        cursor = None

        while True:
            if cursor:
                params["after"] = cursor
            elif "after" in params:
                params.pop("after")

            response = await self._client.get("/channels/followers", params=params)
            try:
                data = await handle_api_response(response, f"get_channel_followers({broadcaster_id})")
                parsed: FollowersResponse = FollowersResponse.model_validate(data)
                followers_page: list[FollowerData] = parsed.data
            except ValidationError:
                break

            followers.extend(
                [
                    ChannelFollowerDTO(
                        user_id=item.user_id,
                        user_name=item.user_login,
                        display_name=item.user_name,
                        followed_at=item.followed_at.replace(tzinfo=None),
                    )
                    for item in followers_page
                ]
            )

            pagination = data.get("pagination") if isinstance(data, dict) else None
            cursor = None if not pagination else pagination.get("cursor")
            if not cursor or not parsed.data:
                break

        return followers

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        user = await self._user_info.get_user_by_login(channel_name)
        broadcaster_id = None if user is None else user.id
        if not broadcaster_id:
            return []
        return await self._get_channel_followers(broadcaster_id=broadcaster_id)
