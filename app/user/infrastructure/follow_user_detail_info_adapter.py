from app.follow.domain.repo import FollowersRepository
from app.user.application.model.user_detail_models import UserDetailInfo
from app.user.application.ports.user_detail_info_port import UserDetailInfoPort


class FollowUserDetailInfoAdapter(UserDetailInfoPort):
    def __init__(self, followers_repo: FollowersRepository):
        self._repo = followers_repo

    def get(self, channel_name: str, user_name: str) -> UserDetailInfo:
        follower = self._repo.get_by_user_name(channel_name, user_name)
        if not follower:
            return UserDetailInfo(
                channel_name=channel_name,
                user_name=user_name,
                display_name=user_name,
                followed_at=None,
                first_seen_at=None,
                last_seen_at=None,
                unfollowed_at=None,
                is_active=False,
                created_at=None,
                updated_at=None,
            )
        return UserDetailInfo(
            channel_name=follower.channel_name,
            user_name=follower.user_name,
            display_name=follower.display_name,
            followed_at=follower.followed_at,
            first_seen_at=follower.first_seen_at,
            last_seen_at=follower.last_seen_at,
            unfollowed_at=follower.unfollowed_at,
            is_active=follower.is_active,
            created_at=follower.created_at,
            updated_at=follower.updated_at,
        )
