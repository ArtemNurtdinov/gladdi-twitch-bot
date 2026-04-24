import asyncio
from datetime import UTC, datetime

from app.core.logger.domain.logger import Logger
from app.task.domain.job import BackgroundJob
from app.viewer.session.application.model.viewer_time import ViewerTimeDTO
from app.viewer.session.application.usecase.reward_viewer_time_use_case import RewardViewerTimeUseCase


class ViewerTimeJob(BackgroundJob):
    CHECK_VIEWER_INTERVAL_SECONDS = 10
    name = "check_viewer_time"

    def __init__(self, handle_viewer_time_use_case: RewardViewerTimeUseCase, logger: Logger):
        self._channel_name: str | None = None
        self._bot_name: str | None = None
        self._handle_viewer_time_use_case = handle_viewer_time_use_case
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str):
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                bot_nick = self._bot_name.lower()
                viewer_time_dto = ViewerTimeDTO(bot_nick=bot_nick, channel_name=self._channel_name, occurred_at=datetime.now(UTC))
                await self._handle_viewer_time_use_case.handle(viewer_time=viewer_time_dto)
                await asyncio.sleep(self.CHECK_VIEWER_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_error(f"Ошибка в ViewerTimeJob: {e}")
                await asyncio.sleep(self.CHECK_VIEWER_INTERVAL_SECONDS)
