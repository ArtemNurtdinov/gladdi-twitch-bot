from app.core.logger.domain.logger import Logger
from app.platform.auth.platform_auth import PlatformAuth


class HandleTokenCheckerUseCase:
    def __init__(self, platform_auth: PlatformAuth, logger: Logger):
        self._platform_auth = platform_auth
        self._logger = logger.create_child(__name__)

    async def handle(self) -> None:
        token_is_valid = await self._platform_auth.check_token_is_valid()
        self._logger.log_info(f"Статус токена: {'действителен' if token_is_valid else 'недействителен'}")
        if not token_is_valid:
            await self._platform_auth.update_access_token()
            self._logger.log_info("Токен обновлён")
