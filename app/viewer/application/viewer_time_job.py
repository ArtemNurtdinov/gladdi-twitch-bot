import asyncio
import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.application.model import ViewerTimeDTO
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class ViewerTimeJob:
    name = "check_viewer_time"

    def __init__(
        self,
        channel_name: str,
        handle_viewer_time_use_case: HandleViewerTimeUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick: str,
        check_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._handle_viewer_time_use_case = handle_viewer_time_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self._bot_nick = bot_nick
        self._interval_seconds = check_interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                bot_nick = self._bot_nick.lower()
                viewer_time_dto = ViewerTimeDTO(bot_nick=bot_nick, channel_name=self._channel_name, occurred_at=datetime.utcnow())

                await self._handle_viewer_time_use_case.handle(
                    db_session_provider=self._db_session_provider,
                    db_readonly_session_provider=self._db_readonly_session_provider,
                    viewer_time_dto=viewer_time_dto,
                )
            except asyncio.CancelledError:
                logger.info("ViewerTimeJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ViewerTimeJob: {e}")

            await asyncio.sleep(self._interval_seconds)
