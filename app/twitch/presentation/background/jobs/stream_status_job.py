import asyncio
import logging
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.presentation.background.model.state import ChatSummaryState
from app.twitch.application.background.stream_status.dto import StatusJobDTO
from app.twitch.application.background.stream_status.handle_stream_status_use_case import HandleStreamStatusUseCase
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class StreamStatusJob:
    name = "check_stream_status"

    def __init__(
        self,
        channel_name: str,
        handle_stream_status_use_case: HandleStreamStatusUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        state: ChatSummaryState,
        stream_status_interval_seconds: int,
    ):
        self._channel_name = channel_name
        self._handle_stream_status_use_case = handle_stream_status_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self._state = state
        self._interval_seconds = stream_status_interval_seconds

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                handle_stream_status = StatusJobDTO(channel_name=self._channel_name)
                await self._handle_stream_status_use_case.handle(
                    db_session_provider=self._db_session_provider,
                    db_readonly_session_provider=self._db_readonly_session_provider,
                    dto=handle_stream_status
                )
            except asyncio.CancelledError:
                logger.info("StreamStatusJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в StreamStatusJob: {e}")

            await asyncio.sleep(self._interval_seconds)
