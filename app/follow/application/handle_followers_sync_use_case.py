from app.follow.application.followers_port import FollowersPort
from app.follow.application.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.follow.application.model import FollowersSyncJobDTO


class HandleFollowersSyncUseCase:
    def __init__(
        self,
        followers_port: FollowersPort,
        unit_of_work_factory: FollowersSyncUnitOfWorkFactory,
    ):
        self._followers_port = followers_port
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(self, sync_job: FollowersSyncJobDTO):
        followers = await self._followers_port.get_channel_followers(sync_job.channel_name)
        seen_at = sync_job.occurred_at

        with self._unit_of_work_factory.create() as uow:
            existing = uow.followers_repo.list_by_channel(sync_job.channel_name)
            existing_map = {f.user_id: f for f in existing}

            new_count = 0
            for follower in followers:
                prev = existing_map.pop(follower.user_id, None)
                if prev is None or not prev.is_active or prev.unfollowed_at:
                    new_count += 1
                uow.followers_repo.upsert_active(
                    channel_name=sync_job.channel_name,
                    user_id=follower.user_id,
                    user_name=follower.user_name,
                    display_name=follower.display_name,
                    followed_at=follower.followed_at,
                    seen_at=seen_at,
                )

            unfollowed_ids = [f.user_id for f in existing_map.values() if f.is_active]
            if unfollowed_ids:
                uow.followers_repo.mark_unfollowed(
                    channel_name=sync_job.channel_name,
                    user_ids=unfollowed_ids,
                    unfollowed_at=seen_at,
                )
