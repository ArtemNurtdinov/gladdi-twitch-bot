from typing import Optional, Protocol

from app.twitch.application.interaction.follow.dto import FollowageInfo


class FollowageProvider(Protocol):

    async def get_followage(self, channel_login: str, user_id: str) -> Optional[FollowageInfo]:
        ...
