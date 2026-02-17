import logging
from datetime import datetime, timedelta

from app.user.application.ports.user_cache_port import UserCachePort
from app.user.application.ports.user_info_port import UserInfoPort

logger = logging.getLogger(__name__)


class UserCacheService(UserCachePort):
    def __init__(self, user_info_port: UserInfoPort, ttl_minutes: int = 30):
        self._user_info_port = user_info_port
        self._ttl = timedelta(minutes=ttl_minutes)
        self._cache: dict[str, tuple[str, datetime]] = {}

    async def get_user_id(self, login: str) -> str | None:
        now = datetime.utcnow()
        cached = self._cache.get(login)
        if cached:
            user_id, cached_at = cached
            if now - cached_at < self._ttl:
                return user_id

        user_info = await self._user_info_port.get_user_by_login(login)
        user_id = None if user_info is None else user_info.id
        if user_id:
            self._cache[login] = (user_id, now)
        return user_id

    async def warmup(self, login: str):
        try:
            await self.get_user_id(login)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID для {login}: {e}")
