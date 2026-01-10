import asyncio
import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.follow.application.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.application.model import FollowersSyncJobDTO
from core.background.task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class FollowersSyncJob:
    name = "sync_followers"

    def __init__(
        self,
        channel_name: str,
        handle_followers_sync_use_case: HandleFollowersSyncUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        interval_seconds: int = 24 * 60 * 60,
    ):
        self._channel_name = channel_name
        self._handle_followers_sync_use_case = handle_followers_sync_use_case
        self._db_session_provider = db_session_provider
        self._interval_seconds = interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                dto = FollowersSyncJobDTO(channel_name=self._channel_name, occurred_at=datetime.utcnow())
                await self._handle_followers_sync_use_case.handle(db_session_provider=self._db_session_provider, sync_job=dto)
            except asyncio.CancelledError:
                logger.info("FollowersSyncJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в FollowersSyncJob: {e}")

            await asyncio.sleep(self._interval_seconds)
