import asyncio

from app.core.logger.domain.logger import Logger
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from core.background.task_runner import BackgroundTaskRunner
from core.background.tasks import BackgroundJob


class StreamStatusJob(BackgroundJob):
    name = "check_stream_status"
    STREAM_STATUS_INTERVAL = 10

    def __init__(self, channel_name: str, handle_stream_status_use_case: HandleStreamStatusUseCase, logger: Logger):
        self._channel_name = channel_name
        self._handle_stream_status_use_case = handle_stream_status_use_case
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await self._handle_stream_status_use_case.handle(channel_name=self._channel_name)
                await asyncio.sleep(self.STREAM_STATUS_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                pass
