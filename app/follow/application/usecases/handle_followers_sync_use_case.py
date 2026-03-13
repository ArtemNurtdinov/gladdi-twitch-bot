from datetime import datetime

from app.follow.application.uow.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.platform.streaming import StreamingPlatformPort


class HandleFollowersSyncUseCase:
    def __init__(self, platform_port: StreamingPlatformPort, sync_followers_uow: FollowersSyncUnitOfWorkFactory):
        self._platform_port = platform_port
        self._sync_followers_uow = sync_followers_uow

    async def handle(self, channel_name: str, seen_at: datetime):
        followers = await self._platform_port.get_channel_followers(channel_name)

        with self._sync_followers_uow.create() as uow:
            existing = uow.followers_repo.list_by_channel(channel_name)
            existing_map = {f.user_id: f for f in existing}

            for follower in followers:
                uow.followers_repo.upsert_active(
                    channel_name=channel_name,
                    user_id=follower.user_id,
                    user_name=follower.user_name,
                    display_name=follower.display_name,
                    followed_at=follower.followed_at,
                    seen_at=seen_at,
                )

            unfollowed_ids = [f.user_id for f in existing_map.values() if f.is_active]
            if unfollowed_ids:
                uow.followers_repo.mark_unfollowed(
                    channel_name=channel_name,
                    user_ids=unfollowed_ids,
                    unfollowed_at=seen_at,
                )
