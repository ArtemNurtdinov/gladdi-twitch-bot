import asyncio

from app.core.logger.domain.logger import Logger
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from core.background.task_runner import BackgroundTaskRunner


class TokenCheckerJob:
    name = "check_token"
    CHECK_INTERVAL_SECONDS = 1000

    def __init__(self, handle_token_checker_use_case: HandleTokenCheckerUseCase, logger: Logger):
        self._handle_token_checker_use_case = handle_token_checker_use_case
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
                await self._handle_token_checker_use_case.handle()
            except asyncio.CancelledError:
                self._logger.log_info("TokenCheckerJob cancelled")
                break
            except Exception as e:
                self._logger.log_exception("Ошибка в TokenCheckerJob:", e)
