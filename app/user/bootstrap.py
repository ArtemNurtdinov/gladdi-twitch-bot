from dataclasses import dataclass

from app.platform.streaming import StreamingPlatformPort
from app.user.application.user_info_port import UserInfoPort
from app.user.infrastructure.cache.user_cache_service import UserCacheService
from app.user.infrastructure.user_info_adapter import UserInfoAdapter


@dataclass
class UserProviders:
    user_info_port: UserInfoPort
    user_cache: UserCacheService


def build_user_providers(platform: StreamingPlatformPort) -> UserProviders:
    user_info_port = UserInfoAdapter(platform)
    user_cache = UserCacheService(user_info_port)
    return UserProviders(
        user_info_port=user_info_port,
        user_cache=user_cache,
    )
