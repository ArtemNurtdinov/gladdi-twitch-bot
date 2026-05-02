from app.core.logger.domain.logger import Logger
from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort


class TimeoutUseCase:
    def __init__(self, platform_repository: PlatformRepository, viewer_cache: ViewerCachePort, logger: Logger):
        self._platform_repository = platform_repository
        self._viewer_cache = viewer_cache
        self._logger = logger.create_child(__name__)

    async def timeout_user(self, channel_name: str, moderator_name: str, username: str, duration_seconds: int, reason: str) -> bool:
        try:
            user_id = await self._viewer_cache.get_viewer_id(username)
            broadcaster_id = await self._viewer_cache.get_viewer_id(channel_name)
            moderator_id = await self._viewer_cache.get_viewer_id(moderator_name)

            if not user_id or not broadcaster_id or not moderator_id:
                self._logger.log_error("Не удалось получить user_id, broadcaster_id или moderator_id")
                return False

            return await self._platform_repository.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
        except Exception as e:
            self._logger.log_error(f"Ошибка при попытке дать таймаут пользователю {username}: {e}")
            return False
