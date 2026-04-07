import asyncio

from app.core.logger.domain.logger import Logger
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.task.domain.job import BackgroundJob


class TokenCheckerJob(BackgroundJob):
    name = "check_token"
    CHECK_INTERVAL_SECONDS = 1000

    def __init__(self, handle_token_checker_use_case: HandleTokenCheckerUseCase, logger: Logger):
        self._handle_token_checker_use_case = handle_token_checker_use_case
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str):
        pass

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
                await self._handle_token_checker_use_case.handle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
