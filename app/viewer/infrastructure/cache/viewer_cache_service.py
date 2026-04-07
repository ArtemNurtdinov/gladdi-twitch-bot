from datetime import UTC, datetime, timedelta

from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort


class ViewerCacheService(ViewerCachePort):
    _CACHE_TTL_MINUTES = 60

    def __init__(self, platform_repository: PlatformRepository):
        self._platform_repository = platform_repository
        self._ttl = timedelta(minutes=self._CACHE_TTL_MINUTES)
        self._cache: dict[str, tuple[str, datetime]] = {}

    async def get_viewer_id(self, login: str) -> str | None:
        now = datetime.now(UTC)
        cached = self._cache.get(login)
        if cached:
            user_id, cached_at = cached
            if now - cached_at < self._ttl:
                return user_id

        user_info = await self._platform_repository.get_user_by_login(login)
        user_id = None if user_info is None else user_info.id
        if user_id:
            self._cache[login] = (user_id, now)
        return user_id

    async def warmup(self, login: str):
        await self.get_viewer_id(login)
