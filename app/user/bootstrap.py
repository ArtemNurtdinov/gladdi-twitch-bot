from dataclasses import dataclass

from app.user.application.user_info_port import UserInfoPort
from app.user.infrastructure.cache.user_cache_service import UserCacheService
from app.user.infrastructure.user_info_adapter import UserInfoAdapter
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


@dataclass
class UserProviders:
    user_info_port: UserInfoPort
    user_cache: UserCacheService


def build_user_providers(twitch_api_service: TwitchApiService) -> UserProviders:
    user_info_port = UserInfoAdapter(twitch_api_service)
    user_cache = UserCacheService(user_info_port)
    return UserProviders(
        user_info_port=user_info_port,
        user_cache=user_cache,
    )

