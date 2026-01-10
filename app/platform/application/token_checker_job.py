import asyncio
import logging

from app.platform.handle_token_checker_use_case import HandleTokenCheckerUseCase
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class TokenCheckerJob:
    name = "check_token"

    def __init__(self, handle_token_checker_use_case: HandleTokenCheckerUseCase):
        self._handle_token_checker_use_case = handle_token_checker_use_case
        self._interval_seconds = handle_token_checker_use_case.interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._interval_seconds)
                await self._handle_token_checker_use_case.handle()
            except asyncio.CancelledError:
                logger.info("TokenCheckerJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в TokenCheckerJob: {e}")
