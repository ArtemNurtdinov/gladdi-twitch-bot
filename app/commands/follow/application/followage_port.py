from typing import Optional, Protocol

from app.commands.follow.model import FollowageInfo


class FollowagePort(Protocol):

    async def get_followage(self, channel_name: str, user_id: str) -> Optional[FollowageInfo]:
        ...
