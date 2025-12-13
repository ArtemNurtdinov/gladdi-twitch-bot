from dataclasses import dataclass


@dataclass
class FollowInfo:
    user_id: str
    user_name: str
    user_login: str
    followed_at: str 