from dataclasses import dataclass

from app.platform.domain.repository import PlatformRepository
from app.user.application.ports.user_cache_port import UserCachePort
from app.user.infrastructure.cache.user_cache_service import UserCacheService


@dataclass
class UserProviders:
    user_cache: UserCachePort


def build_user_providers(platform_repository: PlatformRepository) -> UserProviders:
    user_cache = UserCacheService(platform_repository)
    return UserProviders(
        user_cache=user_cache,
    )
