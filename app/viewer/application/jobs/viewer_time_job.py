import asyncio
from datetime import datetime

from app.core.logger.domain.logger import Logger
from app.viewer.application.models.viewer_time import ViewerTimeDTO
from app.viewer.application.usecases.reward_viewer_time_use_case import RewardViewerTimeUseCase
from core.background.task_runner import BackgroundTaskRunner
from core.background.tasks import BackgroundJob


class ViewerTimeJob(BackgroundJob):
    CHECK_VIEWER_INTERVAL_SECONDS = 10
    name = "check_viewer_time"

    def __init__(self, channel_name: str, handle_viewer_time_use_case: RewardViewerTimeUseCase, bot_nick: str, logger: Logger):
        self._channel_name = channel_name
        self._handle_viewer_time_use_case = handle_viewer_time_use_case
        self._bot_nick = bot_nick
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                bot_nick = self._bot_nick.lower()
                viewer_time_dto = ViewerTimeDTO(bot_nick=bot_nick, channel_name=self._channel_name, occurred_at=datetime.utcnow())
                await self._handle_viewer_time_use_case.handle(viewer_time=viewer_time_dto)
            except asyncio.CancelledError:
                self._logger.log_info("ViewerTimeJob cancelled")
                break
            except Exception as e:
                self._logger.log_error(f"Ошибка в ViewerTimeJob: {e}")

            await asyncio.sleep(self.CHECK_VIEWER_INTERVAL_SECONDS)
