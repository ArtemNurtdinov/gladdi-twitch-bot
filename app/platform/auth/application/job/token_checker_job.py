import asyncio
import logging

from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from core.background.task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class TokenCheckerJob:
    name = "check_token"
    CHECK_INTERVAL_SECONDS = 1000

    def __init__(self, handle_token_checker_use_case: HandleTokenCheckerUseCase):
        self._handle_token_checker_use_case = handle_token_checker_use_case

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
                await self._handle_token_checker_use_case.handle()
            except asyncio.CancelledError:
                logger.info("TokenCheckerJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в TokenCheckerJob: {e}")
