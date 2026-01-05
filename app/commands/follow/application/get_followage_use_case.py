from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.model import FollowageInfo


class GetFollowageUseCase:
    def __init__(self, followage_port: FollowagePort):
        self._followage_port = followage_port

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        return await self._followage_port.get_followage(channel_name=channel_name, user_id=user_id)
