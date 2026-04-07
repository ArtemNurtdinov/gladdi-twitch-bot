import asyncio
from datetime import UTC, datetime

from app.core.logger.domain.logger import Logger
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.task.domain.job import BackgroundJob


class FollowersSyncJob(BackgroundJob):
    SYNC_FOLLOWERS_INTERVAL_SECONDS = 24 * 60 * 60
    name = "sync_followers"

    def __init__(self, handle_followers_sync_use_case: HandleFollowersSyncUseCase, logger: Logger):
        self._channel_name: str | None = None
        self._bot_name: str | None = None
        self._handle_followers_sync_use_case = handle_followers_sync_use_case
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str):
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                await self._handle_followers_sync_use_case.handle(self._channel_name, datetime.now(UTC))
            except asyncio.CancelledError:
                self._logger.log_info("FollowersSyncJob cancelled")
                break
            except Exception as e:
                self._logger.log_exception("Ошибка в FollowersSyncJob:", e)

            await asyncio.sleep(self.SYNC_FOLLOWERS_INTERVAL_SECONDS)
