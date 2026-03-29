import asyncio
from datetime import datetime

from app.core.logger.domain.logger import Logger
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from core.background.task_runner import BackgroundTaskRunner


class FollowersSyncJob:
    SYNC_FOLLOWERS_INTERVAL_SECONDS = 24 * 60 * 60
    name = "sync_followers"

    def __init__(self, channel_name: str, handle_followers_sync_use_case: HandleFollowersSyncUseCase, logger: Logger):
        self._channel_name = channel_name
        self._handle_followers_sync_use_case = handle_followers_sync_use_case
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await self._handle_followers_sync_use_case.handle(self._channel_name, datetime.utcnow())
            except asyncio.CancelledError:
                self._logger.log_info("FollowersSyncJob cancelled")
                break
            except Exception as e:
                self._logger.log_exception("Ошибка в FollowersSyncJob:", e)

            await asyncio.sleep(self.SYNC_FOLLOWERS_INTERVAL_SECONDS)
