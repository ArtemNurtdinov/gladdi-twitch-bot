import asyncio
import logging
from datetime import datetime

from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.application.model import ViewerTimeDTO
from core.background.task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class ViewerTimeJob:
    name = "check_viewer_time"

    def __init__(
        self,
        channel_name: str,
        handle_viewer_time_use_case: HandleViewerTimeUseCase,
        bot_nick: str,
        check_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._handle_viewer_time_use_case = handle_viewer_time_use_case
        self._bot_nick = bot_nick
        self._interval_seconds = check_interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                bot_nick = self._bot_nick.lower()
                viewer_time_dto = ViewerTimeDTO(bot_nick=bot_nick, channel_name=self._channel_name, occurred_at=datetime.utcnow())

                await self._handle_viewer_time_use_case.handle(viewer_time_dto=viewer_time_dto)
            except asyncio.CancelledError:
                logger.info("ViewerTimeJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ViewerTimeJob: {e}")

            await asyncio.sleep(self._interval_seconds)
