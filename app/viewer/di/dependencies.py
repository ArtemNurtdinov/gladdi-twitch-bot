from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from app.viewer.infrastructure.cache.viewer_cache_service import ViewerCacheService


def provide_viewer_cache(platform_repository: PlatformRepository) -> ViewerCachePort:
    return ViewerCacheService(platform_repository)
