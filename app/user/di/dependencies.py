from app.platform.domain.repository import PlatformRepository
from app.user.application.ports.user_cache_port import UserCachePort
from app.user.infrastructure.cache.user_cache_service import UserCacheService


def provide_user_cache(platform_repository: PlatformRepository) -> UserCachePort:
    return UserCacheService(platform_repository)
