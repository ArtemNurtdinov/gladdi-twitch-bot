from app.commands.follow.application.followage_uow import FollowageUnitOfWorkFactory
from app.commands.follow.application.model import FollowageInfo


class GetFollowageUseCase:
    def __init__(self, unit_of_work_factory: FollowageUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return await uow.followage_port.get_followage(channel_name=channel_name, user_id=user_id)
