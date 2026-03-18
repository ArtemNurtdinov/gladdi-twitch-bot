import asyncio

from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from core.background.task_runner import BackgroundTaskRunner


class StreamStatusJob:
    name = "check_stream_status"
    STREAM_STATUS_INTERVAL = 300

    def __init__(self, channel_name: str, handle_stream_status_use_case: HandleStreamStatusUseCase):
        self._channel_name = channel_name
        self._handle_stream_status_use_case = handle_stream_status_use_case

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await self._handle_stream_status_use_case.handle(channel_name=self._channel_name)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

            await asyncio.sleep(self.STREAM_STATUS_INTERVAL)
