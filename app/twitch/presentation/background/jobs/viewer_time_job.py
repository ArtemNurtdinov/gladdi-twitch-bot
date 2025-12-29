import asyncio
import logging
from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.background.viewer_time.dto import ViewerTimeDTO
from app.twitch.application.background.viewer_time.handle_viewer_time_use_case import HandleViewerTimeUseCase
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class ViewerTimeJob:
    name = "check_viewer_time"

    def __init__(
        self,
        channel_name: str,
        handle_viewer_time_use_case: HandleViewerTimeUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        check_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._handle_viewer_time_use_case = handle_viewer_time_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self._bot_nick_provider = bot_nick_provider
        self._interval_seconds = check_interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                viewer_time_dto = ViewerTimeDTO(
                    bot_nick=self._bot_nick_provider().lower(),
                    channel_name=self._channel_name,
                    occurred_at=datetime.utcnow()
                )

                await self._handle_viewer_time_use_case.handle(
                    db_session_provider=self._db_session_provider,
                    db_readonly_session_provider=self._db_readonly_session_provider,
                    viewer_time_dto=viewer_time_dto
                )
            except asyncio.CancelledError:
                logger.info("ViewerTimeJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ViewerTimeJob: {e}")

            await asyncio.sleep(self._interval_seconds)
