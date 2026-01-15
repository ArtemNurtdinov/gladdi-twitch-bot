import logging

from app.platform.auth import PlatformAuth

logger = logging.getLogger(__name__)


class HandleTokenCheckerUseCase:
    def __init__(self, platform_auth: PlatformAuth, interval_seconds: int):
        self._platform_auth = platform_auth
        self._interval_seconds = interval_seconds

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    async def handle(self) -> None:
        token_is_valid = await self._platform_auth.check_token_is_valid()
        logger.info(f"Статус токена: {'действителен' if token_is_valid else 'недействителен'}")
        if not token_is_valid:
            await self._platform_auth.update_access_token()
            logger.info("Токен обновлён")
