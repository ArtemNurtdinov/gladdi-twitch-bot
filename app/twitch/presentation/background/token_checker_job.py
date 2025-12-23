import asyncio
import logging

from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class TokenCheckerJob:
    name = "check_token"

    def __init__(self, twitch_auth, interval_seconds: int = 1000):
        self._twitch_auth = twitch_auth
        self._interval_seconds = interval_seconds

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._interval_seconds)
                token_is_valid = self._twitch_auth.check_token_is_valid()
                logger.info(f"Статус токена: {'действителен' if token_is_valid else 'недействителен'}")
                if not token_is_valid:
                    self._twitch_auth.update_access_token()
                    logger.info("Токен обновлён")
            except asyncio.CancelledError:
                logger.info("TokenCheckerJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в TokenCheckerJob: {e}")

