import asyncio
import logging

from app.stream.application.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.model import StatusJobDTO
from core.background.task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class StreamStatusJob:
    name = "check_stream_status"

    def __init__(
        self,
        channel_name: str,
        handle_stream_status_use_case: HandleStreamStatusUseCase,
        stream_status_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._handle_stream_status_use_case = handle_stream_status_use_case
        self._interval_seconds = stream_status_interval_seconds

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                handle_stream_status = StatusJobDTO(channel_name=self._channel_name)
                await self._handle_stream_status_use_case.handle(status_job_dto=handle_stream_status)
            except asyncio.CancelledError:
                logger.info("StreamStatusJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в StreamStatusJob: {e}")

            await asyncio.sleep(self._interval_seconds)
