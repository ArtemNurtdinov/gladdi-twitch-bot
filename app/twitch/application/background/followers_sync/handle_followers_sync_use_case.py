from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.background.followers_sync.model import FollowersSyncJobDTO
from app.twitch.application.common.followers_port import FollowersPort
from app.follow.domain.repo import FollowersRepository
from core.provider import Provider


class HandleFollowersSyncUseCase:

    def __init__(
        self,
        followers_port: FollowersPort,
        followers_repository_provider: Provider[FollowersRepository],
    ):
        self._followers_port = followers_port
        self._followers_repository_provider = followers_repository_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        sync_job: FollowersSyncJobDTO
    ):
        followers = await self._followers_port.get_channel_followers(sync_job.channel_name)
        seen_at = sync_job.occurred_at

        with db_session_provider() as db:
            repo = self._followers_repository_provider.get(db)
            existing = repo.list_by_channel(sync_job.channel_name)
            existing_map = {f.user_id: f for f in existing}

            new_count = 0
            for follower in followers:
                prev = existing_map.pop(follower.user_id, None)
                if prev is None or not prev.is_active or prev.unfollowed_at:
                    new_count += 1
                repo.upsert_active(
                    channel_name=sync_job.channel_name,
                    user_id=follower.user_id,
                    user_name=follower.user_name,
                    display_name=follower.display_name,
                    followed_at=follower.followed_at,
                    seen_at=seen_at
                )

            unfollowed_ids = [f.user_id for f in existing_map.values() if f.is_active]
            if unfollowed_ids:
                repo.mark_unfollowed(
                    channel_name=sync_job.channel_name,
                    user_ids=unfollowed_ids,
                    unfollowed_at=seen_at
                )
