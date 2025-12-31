import logging
from typing import Optional

from app.twitch.infrastructure.auth import TwitchAuth

logger = logging.getLogger(__name__)


class HandleTokenCheckerUseCase:

    def __init__(self, twitch_auth: TwitchAuth, interval_seconds: int):
        self._twitch_auth = twitch_auth
        self._interval_seconds = interval_seconds

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    async def handle(self) -> Optional[str]:
        token_is_valid = await self._twitch_auth.check_token_is_valid()
        logger.info(f"Статус токена: {'действителен' if token_is_valid else 'недействителен'}")
        if not token_is_valid:
            await self._twitch_auth.update_access_token()
            logger.info("Токен обновлён")
            return "token_refreshed"
        return None
